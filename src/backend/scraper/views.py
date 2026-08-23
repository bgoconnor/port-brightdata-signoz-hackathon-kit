import json
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from .models import Attempt, DemoSite, Paper, Reproduction, ScrapeRun
from .port_job import KubernetesJobError, create_demo_site_job
from .services import BrightDataError, control_scrape, refresh_scrape, start_scrape


def _serialize_run(run: ScrapeRun) -> dict:
    return {
        'id': run.id,
        'collector_id': run.collector_id,
        'target_url': run.target_url,
        'bright_job_id': run.bright_job_id,
        'status': run.status,
        'bright_status': run.bright_status,
        'records_received': run.records_received,
        'records_written': run.records_written,
        'failure_count': run.failure_count,
        'error': run.error,
        'created_at': run.created_at.isoformat(),
        'updated_at': run.updated_at.isoformat(),
        'bright_started_at': run.bright_started_at.isoformat() if run.bright_started_at else None,
        'bright_finished_at': run.bright_finished_at.isoformat() if run.bright_finished_at else None,
        'completed_at': run.completed_at.isoformat() if run.completed_at else None,
    }


def _serialize_paper(paper: Paper) -> dict:
    """List-shape paper per API.md.

    `abstract` is included: the dataset is small enough that omitting it buys
    nothing, and the detail call must return it anyway.
    """
    return {
        'paper_id': paper.paper_id,
        'arxiv_id': paper.arxiv_id,
        'title': paper.title,
        'authors': paper.authors,
        'abstract': paper.abstract,
        'subjects': paper.subjects,
        'score': paper.score,
        'reproducible': paper.reproducible,
        'scraped_at': paper.scraped_at.isoformat(),
        'source': paper.source,
        'source_id': paper.source_id,
        'source_url': paper.source_url or paper.full_text_source_url or paper.pdf_url,
        'status': paper.status or Paper.Status.INGESTED,
        'retry_count': paper.retry_count,
        # Bright Data full-text enrichment (from the complete-paper runtime)
        'enriched': bool(paper.full_text),
        'full_text_source_url': paper.full_text_source_url,
        'full_text_sha256': paper.full_text_sha256,
        'full_text_acquired_at': (
            paper.full_text_acquired_at.isoformat()
            if paper.full_text_acquired_at
            else None
        ),
    }


def _serialize_attempt(attempt: Attempt) -> dict:
    return {
        'index': attempt.index,
        'status': attempt.status,
        'code': attempt.code,
        'output': attempt.output,
        'duration_s': attempt.duration_s,
        'finished_at': attempt.finished_at.isoformat() if attempt.finished_at else None,
    }


def _serialize_detail(paper: Paper) -> dict:
    """Detail-shape paper per API.md: list fields plus reproduction evidence."""
    data = _serialize_paper(paper)
    repro = getattr(paper, 'reproduction', None)
    if repro is None:
        data.update(
            {
                'generated_code': '',
                'run_output': '',
                'review_note': '',
                'repro_summary': '',
                'evidence_url': '',
                'repro_result': None,
                'attempts': [],
            }
        )
        return data

    data.update(
        {
            'generated_code': repro.generated_code,
            'run_output': repro.run_output,
            'review_note': repro.review_note,
            'repro_summary': repro.repro_summary,
            'evidence_url': repro.evidence_url,
            'repro_result': repro.repro_result,
            'attempts': [_serialize_attempt(a) for a in repro.attempts.all()],
        }
    )
    return data


@require_GET
def summary(request):
    """Header figures per API.md.

    `pass_rate` is a 0-1 fraction over ATTEMPTS (clean runs / total attempts),
    not over papers. `reproductions_attempted` counts papers dispatched to the
    agent at least once.
    """
    total_attempts = Attempt.objects.count()
    passed_attempts = Attempt.objects.filter(status=Attempt.Status.PASSED).count()
    pass_rate = (passed_attempts / total_attempts) if total_attempts else None

    return JsonResponse(
        {
            'papers_ingested': Paper.objects.count(),
            'reproductions_attempted': Reproduction.objects.count(),
            'pass_rate': pass_rate,
            'awaiting_review': Paper.objects.filter(
                status=Paper.Status.AWAITING_REVIEW
            ).count(),
        }
    )


@require_GET
def papers(request):
    queryset = Paper.objects.order_by('-score', 'title')
    data = [_serialize_paper(paper) for paper in queryset]
    return JsonResponse({'count': len(data), 'papers': data})


@require_GET
def paper_detail(request, paper_id: str):
    paper = get_object_or_404(
        Paper.objects.prefetch_related('reproduction__attempts'), pk=paper_id
    )
    return JsonResponse(_serialize_detail(paper))


@csrf_exempt
@require_POST
def paper_review(request, paper_id: str):
    """Record an approve/reject decision.

    Idempotent: repeating the same decision returns the same payload with 200.
    Port remains the system of record; the sync layer propagates the decision.
    """
    paper = get_object_or_404(Paper, pk=paper_id)

    try:
        payload = json.loads(request.body or b'{}')
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Body must be JSON'}, status=400)

    decision = str(payload.get('decision') or '').strip().lower()
    if decision not in {'approve', 'reject'}:
        return JsonResponse(
            {'error': "decision must be 'approve' or 'reject'"}, status=400
        )

    target = (
        Paper.Status.APPROVED if decision == 'approve' else Paper.Status.REJECTED
    )
    if paper.status != target:
        paper.status = target
        paper.save(update_fields=['status'])

    note = payload.get('review_note')
    if note is not None:
        repro, _ = Reproduction.objects.get_or_create(paper=paper)
        repro.review_note = str(note)
        repro.save(update_fields=['review_note'])

    paper.refresh_from_db()
    return JsonResponse(_serialize_detail(paper))


@csrf_exempt
@require_http_methods(['GET', 'POST'])
def scrape_runs(request):
    if request.method == 'POST':
        run = start_scrape()
        status = 201 if run.status != ScrapeRun.Status.FAILED else 502
        return JsonResponse({'run': _serialize_run(run)}, status=status)
    runs = ScrapeRun.objects.all()[:20]
    return JsonResponse({'runs': [_serialize_run(run) for run in runs]})


@csrf_exempt
@require_POST
def scrape_run_action(request, run_id: int, action: str):
    run = get_object_or_404(ScrapeRun, pk=run_id)
    if action == 'refresh':
        run = refresh_scrape(run)
    elif action in {'pause', 'resume', 'cancel'}:
        run = control_scrape(run, action)
    else:
        return JsonResponse({'error': f'Unsupported action: {action}'}, status=400)
    status = 200 if run.status != ScrapeRun.Status.FAILED else 502
    return JsonResponse({'run': _serialize_run(run)}, status=status)


@csrf_exempt
@require_POST
def build_demo_site(request):
    """Launch a one-off job that asks Port to generate a paper demo site."""
    try:
        payload = json.loads(request.body or b'{}')
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Request body must be valid JSON'}, status=400)
    paper_id = str(payload.get('paper_id') or '').strip()
    if not paper_id:
        return JsonResponse({'error': 'paper_id is required'}, status=400)
    paper = get_object_or_404(Paper, pk=paper_id)
    if not paper.full_text.strip():
        return JsonResponse(
            {'error': 'Paper has no full text; refusing an abstract-only demo'},
            status=409,
        )
    try:
        site, _ = DemoSite.objects.get_or_create(paper=paper)
        site.status = DemoSite.Status.QUEUED
        site.error = ''
        site.save(update_fields=['status', 'error', 'updated_at'])
        job_name = create_demo_site_job(paper.paper_id)
    except KubernetesJobError as error:
        return JsonResponse({'error': str(error)}, status=502)
    return JsonResponse(
        {'paper_id': paper.paper_id, 'job_name': job_name, 'status': 'queued'},
        status=202,
    )


@require_GET
def demo_site_status(request, paper_id: str):
    paper = get_object_or_404(Paper, pk=paper_id)
    site = get_object_or_404(DemoSite, paper=paper)
    return JsonResponse({
        'paper_id': paper.paper_id,
        'status': site.status,
        'summary': site.summary,
        'iteration': site.iteration,
        'port_workflow_run_id': site.port_workflow_run_id,
        'job_name': site.job_name,
        'error': site.error,
        'site_url': f'/api/demo-sites/{paper.paper_id}/' if site.status == DemoSite.Status.READY else None,
        'attempts': [
            {
                'iteration': attempt.iteration,
                'port_workflow_run_id': attempt.port_workflow_run_id,
                'status': attempt.status,
                'observations': attempt.observations,
            }
            for attempt in site.attempts.all()
        ],
    })


@require_GET
def demo_site(request, paper_id: str):
    paper = get_object_or_404(Paper, pk=paper_id)
    site = get_object_or_404(DemoSite, paper=paper, status=DemoSite.Status.READY)
    response = HttpResponse(site.html, content_type='text/html; charset=utf-8')
    response['Content-Security-Policy'] = (
        "default-src 'none'; style-src 'unsafe-inline'; script-src 'unsafe-inline'; "
        "img-src data:; font-src data:; base-uri 'none'; form-action 'none'"
    )
    response['X-Content-Type-Options'] = 'nosniff'
    return response
