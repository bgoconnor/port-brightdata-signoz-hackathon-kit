# Local Minikube deployment

Run these commands from the repository root.

## Prerequisites

- Docker
- Minikube
- `kubectl`

## Start the project

Start Minikube if it is not already running:

```bash
minikube start
```

Build and deploy the frontend, backend, and PostgreSQL:

```bash
./src/k8s/deploy_minikube.sh
```

The script creates the `hackathon` namespace, deploys all three containers, and
runs the default Django migrations.

## Access the application

Forward the frontend service:

```bash
kubectl -n hackathon port-forward service/hackathon-frontend 5173:5173
```

Open <http://localhost:5173>. Keep the command running while using the frontend.

To access Django directly, run this in another terminal:

```bash
kubectl -n hackathon port-forward service/hackathon-backend 8000:8000
```

The default Django admin is at <http://localhost:8000/admin/>.

## Check status and logs

```bash
kubectl -n hackathon get deployments,pods,services
kubectl -n hackathon logs -f deployment/hackathon-backend
kubectl -n hackathon logs -f deployment/hackathon-frontend
kubectl -n hackathon logs -f deployment/hackathon-postgres
```

Use `Ctrl-C` to stop following logs or to stop a port-forward.

## Run Django commands

For example:

```bash
kubectl -n hackathon exec deployment/hackathon-backend -- python manage.py check
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
