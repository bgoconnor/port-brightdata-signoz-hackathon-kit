"""Load committed paper records into Postgres.

Bridges Ben's `data/papers.json` (the agreed cross-track contract) into the
Django store so the API serves real rows without spending Bright Data credits.
Idempotent: re-running updates in place and never duplicates.
"""

import json
from datetime import datetime, timezone
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils.dateparse import parse_datetime

from scraper.models import Paper


DEFAULT_SOURCE = 'arXiv'


def _repo_root() -> Path:
    # .../src/backend/scraper/management/commands/load_papers.py -> repo root
    return Path(__file__).resolve().parents[5]


def _parse_scraped_at(value):
    parsed = parse_datetime(value) if isinstance(value, str) else None
    if parsed is None:
        return datetime.now(timezone.utc)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed


class Command(BaseCommand):
    help = 'Load papers from data/papers.json into the database.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--input',
            type=Path,
            default=None,
            help='Path to papers.json (default: <repo root>/data/papers.json)',
        )

    def handle(self, *args, **options):
        path = options['input'] or (_repo_root() / 'data' / 'papers.json')
        if not path.exists():
            raise CommandError(f'No paper file at {path}')

        try:
            records = json.loads(path.read_text())
        except json.JSONDecodeError as error:
            raise CommandError(f'{path} is not valid JSON: {error}') from error

        if isinstance(records, dict):
            records = records.get('papers', [])
        if not isinstance(records, list):
            raise CommandError('Expected a list of papers')

        created = updated = skipped = 0
        with transaction.atomic():
            for raw in records:
                arxiv_id = str(raw.get('arxiv_id') or '').strip()
                if not arxiv_id:
                    skipped += 1
                    continue

                _, was_created = Paper.objects.update_or_create(
                    arxiv_id=arxiv_id,
                    defaults={
                        'title': str(raw.get('title') or '').strip(),
                        'authors': raw.get('authors') or [],
                        'abstract': str(raw.get('abstract') or '').strip(),
                        'subjects': raw.get('subjects') or [],
                        'score': float(raw.get('score') or 0.0),
                        'reproducible': bool(raw.get('reproducible')),
                        'scraped_at': _parse_scraped_at(raw.get('scraped_at')),
                        'source': str(raw.get('source') or DEFAULT_SOURCE),
                        'source_url': raw.get('source_url')
                        or f'https://arxiv.org/abs/{arxiv_id}',
                    },
                )
                created += was_created
                updated += not was_created

        self.stdout.write(
            self.style.SUCCESS(
                f'Loaded {created + updated} papers from {path} '
                f'({created} created, {updated} updated, {skipped} skipped)'
            )
        )
