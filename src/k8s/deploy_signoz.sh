#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SIGNOZ_NAMESPACE="${SIGNOZ_NAMESPACE:-hackathon}"
SIGNOZ_CHART_VERSION="${SIGNOZ_CHART_VERSION:-0.138.0}"

for required_command in helm kubectl; do
  if ! command -v "${required_command}" >/dev/null 2>&1; then
    echo "Missing required command: ${required_command}"
    exit 1
  fi
done

CURRENT_CONTEXT="$(kubectl config current-context)"
if [[ "${CURRENT_CONTEXT}" != "minikube" ]]; then
  echo "Refusing to deploy local SigNoz to Kubernetes context '${CURRENT_CONTEXT}'."
  echo "Switch to the minikube context and retry."
  exit 1
fi

helm repo add signoz https://charts.signoz.io --force-update
helm repo update signoz

helm upgrade --install signoz signoz/signoz \
  --namespace "${SIGNOZ_NAMESPACE}" \
  --create-namespace \
  --version "${SIGNOZ_CHART_VERSION}" \
  --values "${SCRIPT_DIR}/signoz-values.yaml" \
  --wait \
  --timeout 1h

# A fresh SigNoz 0.138 install has no organization yet. Its OpAMP manager
# otherwise replaces the collector pipelines with no-op pipelines, preventing
# local applications from sending telemetry before the first UI sign-up.
kubectl -n "${SIGNOZ_NAMESPACE}" patch deployment signoz-otel-collector \
  --type=json \
  -p='[{"op":"replace","path":"/spec/template/spec/containers/0/args","value":["--config=/conf/otel-collector-config.yaml"]}]'
kubectl -n "${SIGNOZ_NAMESPACE}" rollout status deployment/signoz-otel-collector --timeout=5m

kubectl -n "${SIGNOZ_NAMESPACE}" get pods

echo "SigNoz is ready."
echo "Run: kubectl -n ${SIGNOZ_NAMESPACE} port-forward service/signoz 8080:8080"
