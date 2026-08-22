from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from .models import Paper, ScrapeRun
from .services import control_scrape, refresh_scrape, start_scrape


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


@require_GET
def papers(request):
    queryset = Paper.objects.order_by('-score', 'title')
    data = [
        {
            'arxiv_id': paper.arxiv_id,
            'title': paper.title,
            'authors': paper.authors,
            'abstract': paper.abstract,
            'subjects': paper.subjects,
            'score': paper.score,
            'reproducible': paper.reproducible,
            'scraped_at': paper.scraped_at.isoformat(),
            'url': f'https://arxiv.org/abs/{paper.arxiv_id}',
        }
        for paper in queryset
    ]
    return JsonResponse({'count': len(data), 'papers': data})


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
