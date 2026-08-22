#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SIGNOZ_NAMESPACE="${SIGNOZ_NAMESPACE:-hackathon}"
SIGNOZ_CHART_VERSION="${SIGNOZ_CHART_VERSION:-0.138.0}"
SIGNOZ_K8S_INFRA_CHART_VERSION="${SIGNOZ_K8S_INFRA_CHART_VERSION:-0.17.0}"

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

HELM_CONFLICT_ARGS=()
if helm upgrade --help 2>/dev/null | grep -q -- '--force-conflicts'; then
  HELM_CONFLICT_ARGS+=(--force-conflicts)
fi

helm upgrade --install signoz signoz/signoz \
  --namespace "${SIGNOZ_NAMESPACE}" \
  --create-namespace \
  --version "${SIGNOZ_CHART_VERSION}" \
  --values "${SCRIPT_DIR}/signoz-values.yaml" \
  "${HELM_CONFLICT_ARGS[@]}" \
  --wait \
  --timeout 1h

# A fresh SigNoz 0.138 install has no organization yet. Its OpAMP manager
# otherwise replaces the collector pipelines with no-op pipelines, preventing
# local applications and k8s-infra from sending telemetry before UI sign-up.
# Use Helm's field manager so future Helm 4 server-side upgrades remain clean.
kubectl -n "${SIGNOZ_NAMESPACE}" patch deployment signoz-otel-collector \
  --type=json \
  --field-manager=helm \
  -p='[{"op":"replace","path":"/spec/template/spec/containers/0/args","value":["--config=/conf/otel-collector-config.yaml"]}]'
kubectl -n "${SIGNOZ_NAMESPACE}" rollout status deployment/signoz-otel-collector --timeout=5m

helm upgrade --install signoz-k8s-infra signoz/k8s-infra \
  --namespace "${SIGNOZ_NAMESPACE}" \
  --version "${SIGNOZ_K8S_INFRA_CHART_VERSION}" \
  --values "${SCRIPT_DIR}/signoz-k8s-infra-values.yaml" \
  --set-string "otelCollectorEndpoint=http://signoz-otel-collector.${SIGNOZ_NAMESPACE}.svc.cluster.local:4318" \
  --wait \
  --timeout 10m

kubectl -n "${SIGNOZ_NAMESPACE}" rollout status daemonset/signoz-k8s-infra-otel-agent --timeout=5m
kubectl -n "${SIGNOZ_NAMESPACE}" rollout status deployment/signoz-k8s-infra-otel-deployment --timeout=5m

kubectl -n "${SIGNOZ_NAMESPACE}" get pods

echo "SigNoz application and Kubernetes workload monitoring are ready."
echo "Run: kubectl -n ${SIGNOZ_NAMESPACE} port-forward service/signoz 8080:8080"
