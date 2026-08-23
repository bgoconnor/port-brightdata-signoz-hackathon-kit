import json
import os
import re
import time

from django.core.management.base import BaseCommand, CommandError
from opentelemetry import trace

from scraper.models import DemoSite, DemoSiteAttempt, Paper
from scraper.management.commands.port_hello import _port_request


WORKFLOW = 'article_to_demo_site'
MAX_ARTICLE_CHARS = 120_000
MAX_ATTEMPTS = 3


def _validate_html(html):
    errors = []
    lowered = html.lower()
    if len(html) < 800:
        errors.append('HTML is too small to be a useful demo site.')
    for required in ('<!doctype html', '<html', '<body', '</html>'):
        if required not in lowered:
            errors.append(f'Missing required document marker: {required}')
    if re.search(r'''(?:src|href)\s*=\s*["'](?:https?:)?//''', html, re.I):
        errors.append('External network asset detected; all assets must be inline.')
    if '<script' not in lowered:
        errors.append('No interactive JavaScript was provided.')
    return errors


def _workflow_result(token, run_id):
    deadline = time.monotonic() + 600
    while time.monotonic() < deadline:
        payload, _ = _port_request('GET', f'workflows/runs/{run_id}', token=token)
        run = payload.get('workflowRun', payload)
        if run.get('status') == 'COMPLETED':
            if run.get('result') != 'SUCCESS':
                raise CommandError(f'Port workflow failed: {run.get("result")}')
            for node_run in run.get('nodeRuns', []):
                if node_run.get('node', {}).get('identifier') == 'generate_site':
                    response = node_run.get('output', {}).get('response')
                    if not response:
                        raise CommandError('Port AI node completed without a response')
                    try:
                        return json.loads(response)
                    except json.JSONDecodeError as error:
                        raise CommandError('Port AI response was not valid JSON') from error
            raise CommandError('Port run did not contain the generate_site node')
        if run.get('status') in {'FAILED', 'CANCELLED'}:
            raise CommandError(f'Port workflow ended with status {run.get("status")}')
        time.sleep(3)
    raise CommandError('Timed out waiting for Port AI workflow')


class Command(BaseCommand):
    help = 'Ask Port AI to build, validate, and persist an article demo website.'

    def add_arguments(self, parser):
        parser.add_argument('--paper-id', required=True)

    def handle(self, *args, **options):
        try:
            paper = Paper.objects.get(pk=options['paper_id'])
        except Paper.DoesNotExist as error:
            raise CommandError(f'Unknown paper: {options["paper_id"]}') from error
        if not paper.full_text.strip():
            raise CommandError('Paper has no full text; refusing an abstract-only demo')

        client_id = os.environ.get('PORT_CLIENT_ID', '').strip()
        client_secret = os.environ.get('PORT_CLIENT_SECRET', '').strip()
        if not client_id or not client_secret:
            raise CommandError('PORT_CLIENT_ID and PORT_CLIENT_SECRET must be configured')
        auth, _ = _port_request(
            'POST', 'auth/access_token',
            {'clientId': client_id, 'clientSecret': client_secret},
        )
        token = auth.get('accessToken')
        if not token:
            raise CommandError('Port authentication returned no access token')

        site, _ = DemoSite.objects.get_or_create(paper=paper)
        site.status = DemoSite.Status.GENERATING
        site.job_name = os.environ.get('K8S_JOB_NAME', '')
        site.error = ''
        site.save()
        feedback = {'message': 'No prior attempt. Generate the first version.'}
        tracer = trace.get_tracer(__name__)

        for iteration in range(1, MAX_ATTEMPTS + 1):
            with tracer.start_as_current_span('port.demo_site.generate') as span:
                span.set_attribute('article.id', paper.paper_id)
                span.set_attribute('factory.iteration', iteration)
                run_payload, _ = _port_request(
                    'POST', f'workflows/{WORKFLOW}/runs',
                    {
                        'nodeIdentifier': 'trigger',
                        'inputs': {
                            'paper_id': paper.paper_id,
                            'title': paper.title,
                            'article_text': paper.full_text[:MAX_ARTICLE_CHARS],
                            'iteration': iteration,
                            'observability_feedback': json.dumps(feedback),
                        },
                    }, token=token,
                )
                run = run_payload.get('workflowRun', run_payload)
                run_id = run.get('identifier')
                if not run_id:
                    raise CommandError('Port did not return a workflow run identifier')
                generated = _workflow_result(token, run_id)
                html = str(generated.get('html') or '')
                errors = _validate_html(html)
                feedback = {
                    'validator': 'django-demo-site-v1',
                    'iteration': iteration,
                    'errors': errors,
                    'html_bytes': len(html.encode()),
                }
                DemoSiteAttempt.objects.update_or_create(
                    demo_site=site,
                    iteration=iteration,
                    defaults={
                        'port_workflow_run_id': run_id,
                        'status': 'failed' if errors else 'passed',
                        'observations': feedback,
                    },
                )
                span.set_attribute('factory.validation_error_count', len(errors))
                if not errors:
                    site.status = DemoSite.Status.READY
                    site.html = html
                    site.summary = str(generated.get('summary') or '')
                    site.iteration = iteration
                    site.port_workflow_run_id = run_id
                    site.error = ''
                    site.save()
                    self.stdout.write(json.dumps({
                        'event': 'demo_site.ready',
                        'paper_id': paper.paper_id,
                        'iteration': iteration,
                        'port_workflow_run_id': run_id,
                        'site_path': f'/api/demo-sites/{paper.paper_id}/',
                    }))
                    return

        site.status = DemoSite.Status.FAILED
        site.iteration = MAX_ATTEMPTS
        site.error = json.dumps(feedback)
        site.save()
        raise CommandError(f'Demo site failed validation after {MAX_ATTEMPTS} attempts')
