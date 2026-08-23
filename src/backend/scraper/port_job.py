import json
import os
import ssl
import uuid
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from opentelemetry import trace


SERVICE_ACCOUNT_DIR = Path('/var/run/secrets/kubernetes.io/serviceaccount')


class KubernetesJobError(RuntimeError):
    pass


def create_demo_site_job(paper_id: str) -> str:
    job_name = f'demo-site-{uuid.uuid4().hex[:12]}'
    namespace = os.environ.get('POD_NAMESPACE', 'hackathon')
    otel_attributes = os.environ.get(
        'OTEL_RESOURCE_ATTRIBUTES',
        'service.namespace=paper-factory,service.version=local,deployment.environment=local',
    )
    manifest = {
        'apiVersion': 'batch/v1',
        'kind': 'Job',
        'metadata': {
            'name': job_name,
            'namespace': namespace,
            'labels': {'app': 'hackathon-port-job'},
        },
        'spec': {
            'backoffLimit': 0,
            'activeDeadlineSeconds': 900,
            'ttlSecondsAfterFinished': 600,
            'template': {
                'metadata': {'labels': {'app': 'hackathon-port-job'}},
                'spec': {
                    'automountServiceAccountToken': False,
                    'restartPolicy': 'Never',
                    'containers': [{
                        'name': 'port-job',
                        'image': os.environ.get('PORT_JOB_IMAGE', 'hackathon-backend:local'),
                        'imagePullPolicy': 'Never',
                        'command': ['opentelemetry-instrument', 'python', 'manage.py', 'build_demo_site'],
                        'args': ['--paper-id', paper_id],
                        'env': [
                            {'name': 'POSTGRES_HOST', 'value': os.environ.get('POSTGRES_HOST', 'hackathon-postgres')},
                            {'name': 'POSTGRES_DB', 'value': os.environ.get('POSTGRES_DB', 'hackathon')},
                            {'name': 'POSTGRES_USER', 'value': os.environ.get('POSTGRES_USER', 'hackathon')},
                            {'name': 'POSTGRES_PASSWORD', 'value': os.environ.get('POSTGRES_PASSWORD', 'hackathon')},
                            {'name': 'DJANGO_SETTINGS_MODULE', 'value': 'config.settings'},
                            {'name': 'PORT_API_URL', 'value': os.environ.get('PORT_API_URL', 'https://api.port.io/v1')},
                            {
                                'name': 'PORT_CLIENT_ID',
                                'valueFrom': {'secretKeyRef': {'name': 'hackathon-port', 'key': 'PORT_CLIENT_ID'}},
                            },
                            {
                                'name': 'PORT_CLIENT_SECRET',
                                'valueFrom': {'secretKeyRef': {'name': 'hackathon-port', 'key': 'PORT_CLIENT_SECRET'}},
                            },
                            {
                                'name': 'OTEL_EXPORTER_OTLP_ENDPOINT',
                                'value': os.environ.get(
                                    'OTEL_EXPORTER_OTLP_ENDPOINT',
                                    'http://signoz-otel-collector.hackathon.svc.cluster.local:4318',
                                ),
                            },
                            {'name': 'OTEL_EXPORTER_OTLP_PROTOCOL', 'value': 'http/protobuf'},
                            {'name': 'OTEL_SERVICE_NAME', 'value': 'hackathon-port-job'},
                            {
                                'name': 'OTEL_RESOURCE_ATTRIBUTES',
                                'value': f'{otel_attributes},k8s.job.name={job_name}',
                            },
                            {'name': 'OTEL_TRACES_EXPORTER', 'value': 'otlp'},
                            {'name': 'OTEL_METRICS_EXPORTER', 'value': 'otlp'},
                            {'name': 'OTEL_LOGS_EXPORTER', 'value': 'none'},
                            {'name': 'PYTHONUNBUFFERED', 'value': '1'},
                            {'name': 'K8S_JOB_NAME', 'value': job_name},
                        ],
                    }],
                },
            },
        },
    }

    host = os.environ.get('KUBERNETES_SERVICE_HOST', '')
    token_path = SERVICE_ACCOUNT_DIR / 'token'
    ca_path = SERVICE_ACCOUNT_DIR / 'ca.crt'
    if not host or not token_path.exists() or not ca_path.exists():
        raise KubernetesJobError('Kubernetes in-cluster credentials are unavailable')

    request = Request(
        f'https://{host}:{os.environ.get("KUBERNETES_SERVICE_PORT_HTTPS", "443")}'
        f'/apis/batch/v1/namespaces/{namespace}/jobs',
        data=json.dumps(manifest).encode(),
        headers={
            'Authorization': f'Bearer {token_path.read_text().strip()}',
            'Content-Type': 'application/json',
        },
        method='POST',
    )
    try:
        with trace.get_tracer(__name__).start_as_current_span('kubernetes.job.create') as span:
            span.set_attribute('k8s.job.name', job_name)
            span.set_attribute('article.id', paper_id)
            with urlopen(
                request,
                context=ssl.create_default_context(cafile=str(ca_path)),
                timeout=15,
            ):
                pass
    except HTTPError as error:
        raise KubernetesJobError(f'Kubernetes API returned HTTP {error.code}') from error
    except URLError as error:
        raise KubernetesJobError(f'Could not reach Kubernetes API: {error.reason}') from error
    return job_name


def create_port_hello_job(paper_id: str) -> str:
    """Compatibility alias for the original proof-of-connectivity endpoint."""
    return create_demo_site_job(paper_id)
