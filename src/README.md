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

The root `.env` must contain `BRIGHTDATA_API_KEY`. The deploy script loads that
file and creates or updates the `hackathon-brightdata` Kubernetes Secret.

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
the default Django migrations. It installs two pinned official Helm charts in
the same namespace:

- `signoz/signoz` provides the SigNoz UI, ingest collector, and telemetry store.
- `signoz/k8s-infra` provides a node-local collector plus a cluster collector for
  Kubernetes metrics, events, and selected container logs.

The default pinned chart versions are `0.138.0` for `signoz/signoz` and `0.17.0`
for `signoz/k8s-infra`. Override them with `SIGNOZ_CHART_VERSION` and
`SIGNOZ_K8S_INFRA_CHART_VERSION` when deliberately testing an upgrade.

The Django backend sends OpenTelemetry data to the node-local collector, which
adds Kubernetes metadata before forwarding it to SigNoz. Automatic
instrumentation covers Django requests, PostgreSQL calls, Bright Data HTTP calls,
Python process metrics, and trace-correlated application logs.

The workload collectors monitor node, pod, container, deployment, StatefulSet,
and DaemonSet health. Container-file logs are limited to the `hackathon`
namespace; backend container logs are excluded there because the Python SDK
already exports them directly.

To update only SigNoz, run:

```bash
./src/k8s/deploy_signoz.sh
```

After the initial SigNoz installation, rebuild the application without updating
either SigNoz Helm release with:

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
- HTTP, PostgreSQL, and Bright Data child spans carrying `k8s.*` resource
  attributes.
- application metrics and logs filtered by
  `service.name = hackathon-backend`.
- nodes, pods, containers, deployments, StatefulSets, and DaemonSets under
  **Infrastructure -> Kubernetes** with cluster `minikube` and environment
  `local`.
- Kubernetes events and frontend/PostgreSQL container logs under Logs.

Browser-side React telemetry and PostgreSQL server-specific metrics are not
instrumented; PostgreSQL activity is visible through the backend's client spans
and the pod/container workload metrics.

This deployment sends application and Kubernetes telemetry into SigNoz but does
not provision a project-specific dashboard or alert rule.

## Check status and logs

```bash
kubectl -n hackathon get deployments,statefulsets,daemonsets,pods,services
helm list -n hackathon
kubectl -n hackathon logs -f deployment/hackathon-backend
kubectl -n hackathon logs -f deployment/hackathon-frontend
kubectl -n hackathon logs -f deployment/hackathon-postgres
kubectl -n hackathon logs deployment/signoz-otel-collector --tail=100
kubectl -n hackathon logs daemonset/signoz-k8s-infra-otel-agent --tail=100
kubectl -n hackathon logs deployment/signoz-k8s-infra-otel-deployment --tail=100
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
