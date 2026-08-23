# Local Minikube deployment

Run these commands from the repository root.

## Prerequisites

- Docker
- Minikube
- `kubectl`
- Helm 3.8 or newer

Local SigNoz needs a relatively large Minikube profile. The official minimum is
4 CPUs, 8 GB of memory, and 30 GB of storage. Start a fresh profile with those
resources when your current profile is smaller:

```bash
minikube start --memory=8g --cpus=4 --disk-size=30g
```

The root `.env` must contain `BRIGHTDATA_API_KEY`, `BRIGHTDATA_COLLECTOR_ID`, and
`BRIGHTDATA_ANTHROPIC_COLLECTOR_ID`. `BRIGHTDATA_OPENAI_COLLECTOR_ID` is optional
until a healthy OpenAI collector is configured. It must also contain
`PORT_CLIENT_ID` and `PORT_CLIENT_SECRET` from the Port credentials page. The
deploy script loads them and creates or updates the Kubernetes Secrets.
Both Port values are required by the deployment script because the Kubernetes
Job authenticates to Port at runtime.

## Start the project

Start Minikube if it is not already running:

```bash
minikube start
```

Build and deploy the frontend, backend, PostgreSQL, and SigNoz:

```bash
./src/k8s/deploy_minikube.sh
```

The script creates the `hackathon` namespace, deploys the application, and runs
the default Django migrations. It installs pinned official SigNoz Helm charts in
the same namespace. The Django service exports its traces, HTTP and
database metrics, and trace-correlated application logs directly over OTLP.

To update only SigNoz, run:

```bash
./src/k8s/deploy_signoz.sh
```

To rebuild the application without waiting for the SigNoz Helm releases, run:

```bash
HACKATHON_SKIP_SIGNOZ=1 ./src/k8s/deploy_minikube.sh
```

## Access the application

Forward the frontend service:

```bash
kubectl -n hackathon port-forward service/hackathon-frontend 5173:5173
```

Open <http://localhost:5173>. Keep the command running while using the frontend.
The page shows papers stored in PostgreSQL and the latest Bright Data run. Use
**Run Bright scraper** to start a collection; the page polls it until the papers
have been ingested.

To access Django directly, run this in another terminal:

```bash
kubectl -n hackathon port-forward service/hackathon-backend 8000:8000
```

The default Django admin is at <http://localhost:8000/admin/>.

## Trigger the Port hello Job

Choose a `paper_id` returned by `/api/papers/`, then ask Django to create the
one-off Kubernetes Job:

```bash
curl -X POST http://localhost:8000/api/port-hello/ \
  -H 'Content-Type: application/json' \
  -d '{"paper_id":"arxiv:2608.00001"}'
```

The response contains the Job name. Inspect it with:

```bash
kubectl -n hackathon get jobs -l app=hackathon-port-job
kubectl -n hackathon logs job/<job-name>
```

The Job authenticates to Port and performs the read-only hello call
`GET /v1/organization`. It does not create or change anything in Port.

## Access SigNoz

Forward the SigNoz UI in another terminal:

```bash
kubectl -n hackathon port-forward service/signoz 8080:8080
```

Open <http://localhost:8080> and create the local administrator account when
prompted.

Generate traces, metrics, and logs through the project's real paper API:

```bash
curl -fsS http://localhost:8000/api/papers/ | python -m json.tool
curl -fsS http://localhost:8000/api/scrape-runs/ | python -m json.tool
```

In SigNoz, look for:

- `hackathon-backend` under Services and Traces.
- `hackathon-port-job` after triggering the Port hello Job.
- Django HTTP metrics in Metrics Explorer, filtered by
  `service.name = hackathon-backend`.
- application logs filtered by `service.name = hackathon-backend`.

## Check status and logs

```bash
kubectl -n hackathon get deployments,statefulsets,daemonsets,pods,services
helm list -n hackathon
kubectl -n hackathon logs -f deployment/hackathon-backend
kubectl -n hackathon logs -f deployment/hackathon-frontend
kubectl -n hackathon logs -f deployment/hackathon-postgres
kubectl -n hackathon get pods
kubectl -n hackathon logs deployment/signoz-otel-collector --tail=100
```

The deployment follows SigNoz's official
[local Kubernetes installation](https://signoz.io/docs/install/kubernetes/local/)
and [K8s Infra installation](https://signoz.io/docs/opentelemetry-collection-agents/k8s/k8s-infra/install-k8s-infra/)
guides. Use `deploy_signoz.sh` for upgrades because it also applies the local
pre-sign-up collector configuration required by this deployment.

Use `Ctrl-C` to stop following logs or to stop a port-forward.

## Run Django commands

For example:

```bash
kubectl -n hackathon exec deployment/hackathon-backend -- python manage.py check
kubectl -n hackathon exec deployment/hackathon-backend -- python manage.py scrape_papers
kubectl -n hackathon exec deployment/hackathon-backend -- python manage.py scrape_papers --source anthropic
kubectl -n hackathon exec deployment/hackathon-backend -- python manage.py scrape_papers --source openai
kubectl -n hackathon exec -it deployment/hackathon-backend -- python manage.py createsuperuser
```

## Access PostgreSQL

Open a `psql` session inside the PostgreSQL container:

```bash
kubectl -n hackathon exec -it deployment/hackathon-postgres -- psql -U hackathon -d hackathon
```

The local username, password, and database name are all `hackathon`.

## Redeploy or stop

Rebuild and redeploy after changing the code:

```bash
./src/k8s/deploy_minikube.sh
```

Stop Minikube without deleting the cluster:

```bash
minikube stop
```

Remove this project from the cluster:

```bash
kubectl delete namespace hackathon
```

PostgreSQL currently has no persistent volume. Its data is lost if its pod is
replaced or the `hackathon` namespace is deleted.
