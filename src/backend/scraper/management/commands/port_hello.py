import json
import os
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from django.core.management.base import BaseCommand, CommandError
from opentelemetry import trace

from scraper.models import Paper


def _port_request(method, path, payload=None, token=''):
    headers = {'Accept': 'application/json'}
    data = None
    if payload is not None:
        headers['Content-Type'] = 'application/json'
        data = json.dumps(payload).encode()
    if token:
        headers['Authorization'] = f'Bearer {token}'
    request = Request(
        f'{os.environ.get("PORT_API_URL", "https://api.port.io/v1").rstrip("/")}/{path}',
        data=data,
        headers=headers,
        method=method,
    )
    try:
        with urlopen(request, timeout=20) as response:
            body = response.read()
            return json.loads(body) if body else {}, response.status
    except HTTPError as error:
        raise CommandError(f'Port returned HTTP {error.code}') from error
    except URLError as error:
        raise CommandError(f'Could not reach Port: {error.reason}') from error
    except json.JSONDecodeError as error:
        raise CommandError('Port returned invalid JSON') from error


class Command(BaseCommand):
    help = 'Make an article-scoped hello-world call to Port.'

    def add_arguments(self, parser):
        parser.add_argument('--paper-id', required=True)

    def handle(self, *args, **options):
        try:
            paper = Paper.objects.get(pk=options['paper_id'])
        except Paper.DoesNotExist as error:
            raise CommandError(f'Unknown paper: {options["paper_id"]}') from error

        tracer = trace.get_tracer(__name__)
        with tracer.start_as_current_span('article_port_hello') as span:
            span.set_attribute('article.id', paper.paper_id)
            span.set_attribute('article.source', paper.source)
            span.set_attribute('k8s.job.name', os.environ.get('K8S_JOB_NAME', ''))
            client_id = os.environ.get('PORT_CLIENT_ID', '').strip()
            client_secret = os.environ.get('PORT_CLIENT_SECRET', '').strip()
            if not client_id or not client_secret:
                raise CommandError('PORT_CLIENT_ID and PORT_CLIENT_SECRET must be configured')
            with tracer.start_as_current_span('port.authenticate'):
                auth, _ = _port_request(
                    'POST',
                    'auth/access_token',
                    {'clientId': client_id, 'clientSecret': client_secret},
                )
            token = auth.get('accessToken') if isinstance(auth, dict) else None
            if not token:
                raise CommandError('Port authentication returned no access token')
            with tracer.start_as_current_span('port.hello'):
                _, status = _port_request('GET', 'organization', token=token)
            span.set_attribute('port.http.status_code', status)

        self.stdout.write(json.dumps({
            'event': 'port.hello.succeeded',
            'paper_id': paper.paper_id,
            'job_name': os.environ.get('K8S_JOB_NAME', ''),
            'port_http_status': status,
        }))
