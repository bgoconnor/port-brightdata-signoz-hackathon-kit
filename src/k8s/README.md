# Kubernetes deployment

`base/` contains environment-neutral Django and React Deployments and Services.
`overlays/local/` adds the Minikube namespace, local configuration, development secret, and SQLite volume. `overlays/production/` documents the contract for a future production deployment but cannot be applied accidentally.

## Local Minikube

```bash
./src/k8s/deploy_minikube.sh
```

The script checks the active context, builds both images directly into Minikube, applies the local Kustomize overlay, waits for both rollouts, and forwards the application to `http://127.0.0.1:18080`.

For a non-blocking deployment:

```bash
HACKATHON_SKIP_PORT_FORWARD=1 ./src/k8s/deploy_minikube.sh
```

To use another local port:

```bash
HACKATHON_LOCAL_PORT=18081 ./src/k8s/deploy_minikube.sh
```

