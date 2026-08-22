import hashlib
import json
import os
from datetime import datetime
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen

from django.db import transaction
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from .models import Paper, ScrapeRun


BRIGHTDATA_API_URL = 'https://api.brightdata.com'
DEFAULT_TARGET_URL = 'https://arxiv.org/list/cs.AI/new'
REQUIRED_FIELDS = ('arxiv_id', 'title', 'authors', 'abstract', 'subjects')
SCORE_SIGNALS = {
    'algorithm': 0.22,
    'we propose': 0.22,
    'toy': 0.18,
    'synthetic': 0.18,
    'complexity': 0.10,
    'experiment': 0.10,
}


class BrightDataError(RuntimeError):
    pass


def _configuration() -> tuple[str, str, str]:
    api_key = _api_key()
    collector_id = os.environ.get('BRIGHTDATA_COLLECTOR_ID', '').strip()
    target_url = os.environ.get('BRIGHTDATA_TARGET_URL', DEFAULT_TARGET_URL).strip()
    if not collector_id:
        raise BrightDataError('BRIGHTDATA_COLLECTOR_ID is not configured')
    return api_key, collector_id, target_url


def _api_key() -> str:
    api_key = os.environ.get('BRIGHTDATA_API_KEY', '').strip()
    if not api_key:
        raise BrightDataError('BRIGHTDATA_API_KEY is not configured')
    return api_key


def _fulltext_collector_id() -> str:
    collector_id = os.environ.get('BRIGHTDATA_FULLTEXT_COLLECTOR_ID', '').strip()
    if not collector_id:
        raise BrightDataError('BRIGHTDATA_FULLTEXT_COLLECTOR_ID is not configured')
    return collector_id


def _request(method: str, path: str, payload: Any = None) -> bytes:
    api_key = _api_key()
    headers = {'Authorization': f'Bearer {api_key}'}
    data = None
    if payload is not None:
        headers['Content-Type'] = 'application/json'
        data = json.dumps(payload).encode()
    request = Request(
        f'{BRIGHTDATA_API_URL}{path}',
        data=data,
        headers=headers,
        method=method,
    )
    try:
        with urlopen(request, timeout=60) as response:
            return response.read()
    except HTTPError as error:
        detail = error.read().decode(errors='replace')
        raise BrightDataError(f'Bright Data returned HTTP {error.code}: {detail}') from error
    except URLError as error:
        raise BrightDataError(f'Could not reach Bright Data: {error.reason}') from error


def _request_json(method: str, path: str, payload: Any = None) -> Any:
    body = _request(method, path, payload)
    try:
        return json.loads(body)
    except json.JSONDecodeError as error:
        raise BrightDataError('Bright Data returned invalid JSON') from error


def _parse_bright_datetime(value: Any) -> datetime | None:
    if not isinstance(value, str):
        return None
    parsed = parse_datetime(value)
    if parsed is not None and timezone.is_naive(parsed):
        parsed = timezone.make_aware(parsed)
    return parsed


def _string_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str):
        return [item.strip() for item in value.split(',') if item.strip()]
    return []


def _normalize_record(raw: dict[str, Any], scraped_at: datetime) -> dict[str, Any]:
    arxiv_id = str(raw.get('arxiv_id') or raw.get('id') or '').strip()
    if arxiv_id.lower().startswith('arxiv:'):
        arxiv_id = arxiv_id.split(':', 1)[1].strip()
    paper = {
        'arxiv_id': arxiv_id,
        'title': str(raw.get('title') or '').strip(),
        'authors': _string_list(raw.get('authors')),
        'abstract': str(raw.get('abstract') or raw.get('summary') or '').strip(),
        'subjects': _string_list(raw.get('subjects') or raw.get('categories')),
        'scraped_at': scraped_at,
    }
    missing = [field for field in REQUIRED_FIELDS if not paper[field]]
    if missing:
        identity = paper['arxiv_id'] or paper['title'] or '<unknown>'
        raise BrightDataError(f'Paper {identity} is missing required fields: {missing}')
    text = f"{paper['title']} {paper['abstract']}".lower()
    paper['score'] = round(
        min(1.0, sum(weight for term, weight in SCORE_SIGNALS.items() if term in text)),
        2,
    )
    paper['reproducible'] = paper['score'] >= 0.5
    return paper


def _fail_run(run: ScrapeRun, error: Exception) -> ScrapeRun:
    run.status = ScrapeRun.Status.FAILED
    run.error = str(error)
    run.completed_at = timezone.now()
    run.save(update_fields=('status', 'error', 'completed_at', 'updated_at'))
    return run


def start_scrape() -> ScrapeRun:
    try:
        _, collector_id, target_url = _configuration()
    except BrightDataError:
        raise
    run = ScrapeRun.objects.create(collector_id=collector_id, target_url=target_url)
    try:
        query = urlencode({'collector': collector_id, 'queue_next': 1})
        response = _request_json('POST', f'/dca/trigger?{query}', [{'url': target_url}])
        run.bright_job_id = response['collection_id']
        run.status = ScrapeRun.Status.COLLECTING
        run.error = ''
        run.save(update_fields=('bright_job_id', 'status', 'error', 'updated_at'))
    except (BrightDataError, KeyError, TypeError) as error:
        _fail_run(run, error)
    return run


def start_enrichment(paper: Paper) -> ScrapeRun:
    """Trigger the hosted full-text collector for one already-discovered paper."""
    collector_id = _fulltext_collector_id()
    target_url = f'https://arxiv.org/html/{paper.arxiv_id}'
    run = ScrapeRun.objects.create(
        collector_id=collector_id,
        target_url=target_url,
        kind=ScrapeRun.Kind.ENRICHMENT,
        paper=paper,
    )
    try:
        query = urlencode({'collector': collector_id, 'queue_next': 1})
        response = _request_json('POST', f'/dca/trigger?{query}', [{'url': target_url}])
        run.bright_job_id = response['collection_id']
        run.status = ScrapeRun.Status.COLLECTING
        run.save(update_fields=('bright_job_id', 'status', 'updated_at'))
    except (BrightDataError, KeyError, TypeError) as error:
        _fail_run(run, error)
    return run


def _extract_full_text(response: Any) -> str:
    records = response if isinstance(response, list) else [response]
    if not records or not isinstance(records[0], dict):
        raise BrightDataError('Full-text collector returned an invalid dataset')
    record = records[0]
    text = record.get('full_text') or record.get('markdown') or record.get('content')
    if not isinstance(text, str) or len(text.strip()) < 1000:
        raise BrightDataError('Full-text collector returned too little paper content')
    return text.strip()


def _ingest_enrichment(run: ScrapeRun) -> ScrapeRun:
    if run.paper_id is None:
        raise BrightDataError('Enrichment run is not associated with a paper')
    run.status = ScrapeRun.Status.INGESTING
    run.save(update_fields=('status', 'updated_at'))
    response = _request_json('GET', f'/dca/dataset?{urlencode({"id": run.bright_job_id})}')
    if isinstance(response, dict) and 'status' in response and not any(
        field in response for field in ('full_text', 'markdown', 'content')
    ):
        run.status = ScrapeRun.Status.COLLECTING
        run.bright_status = str(response.get('status') or run.bright_status)
        run.save(update_fields=('status', 'bright_status', 'updated_at'))
        return run

    text = _extract_full_text(response)
    acquired_at = run.bright_finished_at or timezone.now()
    with transaction.atomic():
        paper = Paper.objects.select_for_update().get(pk=run.paper_id)
        paper.full_text = text
        paper.full_text_source_url = run.target_url
        paper.full_text_sha256 = hashlib.sha256(text.encode()).hexdigest()
        paper.full_text_acquired_at = acquired_at
        paper.full_text_collection_id = run.bright_job_id or ''
        paper.save(update_fields=(
            'full_text', 'full_text_source_url', 'full_text_sha256',
            'full_text_acquired_at', 'full_text_collection_id',
        ))
        run.records_received = 1
        run.records_written = 1
        run.status = ScrapeRun.Status.COMPLETED
        run.completed_at = timezone.now()
        run.error = ''
        run.save(update_fields=(
            'records_received', 'records_written', 'status', 'completed_at',
            'error', 'updated_at',
        ))
    return run


def _ingest_results(run: ScrapeRun) -> ScrapeRun:
    run.status = ScrapeRun.Status.INGESTING
    run.error = ''
    run.save(update_fields=('status', 'error', 'updated_at'))

    response = _request_json(
        'GET',
        f'/dca/dataset?{urlencode({"id": run.bright_job_id})}',
    )
    if isinstance(response, dict):
        run.status = ScrapeRun.Status.COLLECTING
        run.bright_status = str(response.get('status') or run.bright_status)
        run.save(update_fields=('status', 'bright_status', 'updated_at'))
        return run
    if not isinstance(response, list) or not response:
        raise BrightDataError('Bright Data completed without any paper records')

    scraped_at = run.bright_finished_at or timezone.now()
    records = [_normalize_record(record, scraped_at) for record in response]
    papers = [Paper(**record) for record in records]
    with transaction.atomic():
        Paper.objects.bulk_create(
            papers,
            update_conflicts=True,
            unique_fields=('arxiv_id',),
            update_fields=(
                'title', 'authors', 'abstract', 'subjects',
                'score', 'reproducible', 'scraped_at',
            ),
        )
        run.records_received = len(records)
        run.records_written = len(records)
        run.status = ScrapeRun.Status.COMPLETED
        run.completed_at = timezone.now()
        run.error = ''
        run.save(update_fields=(
            'records_received', 'records_written', 'status',
            'completed_at', 'error', 'updated_at',
        ))
    return run


def refresh_scrape(run: ScrapeRun) -> ScrapeRun:
    if not run.bright_job_id:
        return _fail_run(run, BrightDataError('Scrape run has no Bright Data job ID'))
    if run.status == ScrapeRun.Status.COMPLETED:
        return run
    try:
        metadata = _request_json('GET', f'/dca/log/{quote(run.bright_job_id)}')
        bright_status = str(metadata.get('status') or '')
        run.bright_status = bright_status
        run.records_received = int(metadata.get('lines') or run.records_received)
        run.failure_count = int(metadata.get('fails') or 0)
        run.bright_started_at = _parse_bright_datetime(metadata.get('started'))
        run.bright_finished_at = _parse_bright_datetime(metadata.get('finished'))

        if bright_status == 'done':
            run.save(update_fields=(
                'bright_status', 'records_received', 'failure_count',
                'bright_started_at', 'bright_finished_at', 'updated_at',
            ))
            if run.kind == ScrapeRun.Kind.ENRICHMENT:
                return _ingest_enrichment(run)
            return _ingest_results(run)
        if bright_status == 'paused':
            run.status = ScrapeRun.Status.PAUSED
        elif bright_status in {'canceled', 'cancelled'}:
            run.status = ScrapeRun.Status.CANCELED
            run.completed_at = timezone.now()
        elif bright_status in {'failed', 'error'}:
            run.status = ScrapeRun.Status.FAILED
            run.completed_at = timezone.now()
            run.error = f'Bright Data job ended with status {bright_status}'
        else:
            run.status = ScrapeRun.Status.COLLECTING
            run.completed_at = None
            run.error = ''
        run.save(update_fields=(
            'bright_status', 'status', 'records_received', 'failure_count',
            'bright_started_at', 'bright_finished_at', 'completed_at',
            'error', 'updated_at',
        ))
    except (BrightDataError, KeyError, TypeError, ValueError) as error:
        _fail_run(run, error)
    return run


def control_scrape(run: ScrapeRun, action: str) -> ScrapeRun:
    statuses = {
        'pause': ScrapeRun.Status.PAUSED,
        'resume': ScrapeRun.Status.COLLECTING,
        'cancel': ScrapeRun.Status.CANCELED,
    }
    if action not in statuses:
        raise ValueError(f'Unsupported scrape action: {action}')
    if not run.bright_job_id:
        return _fail_run(run, BrightDataError('Scrape run has no Bright Data job ID'))
    try:
        _request('POST', f'/dca/jobs/{quote(run.bright_job_id)}/{action}')
        run.status = statuses[action]
        run.bright_status = statuses[action]
        run.error = ''
        if action == 'cancel':
            run.completed_at = timezone.now()
        run.save(update_fields=('status', 'bright_status', 'error', 'completed_at', 'updated_at'))
    except BrightDataError as error:
        _fail_run(run, error)
    return run
