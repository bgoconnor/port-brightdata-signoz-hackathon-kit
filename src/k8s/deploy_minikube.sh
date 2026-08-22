#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
REPO_ROOT="$(cd "${SRC_ROOT}/.." && pwd)"
ENV_FILE="${REPO_ROOT}/.env"

if [[ ! -f "${ENV_FILE}" ]]; then
  echo "Missing ${ENV_FILE}. Copy .env.example to .env and set BRIGHTDATA_API_KEY."
  exit 1
fi

set -a
source "${ENV_FILE}"
set +a

: "${BRIGHTDATA_API_KEY:?BRIGHTDATA_API_KEY must be set in ${ENV_FILE}}"
: "${BRIGHTDATA_COLLECTOR_ID:?BRIGHTDATA_COLLECTOR_ID must be set in ${ENV_FILE}}"
: "${BRIGHTDATA_ANTHROPIC_COLLECTOR_ID:?BRIGHTDATA_ANTHROPIC_COLLECTOR_ID must be set in ${ENV_FILE}}"

kubectl create namespace hackathon --dry-run=client -o yaml | kubectl apply -f -
kubectl -n hackathon create secret generic hackathon-brightdata \
  --from-literal=BRIGHTDATA_API_KEY="${BRIGHTDATA_API_KEY}" \
  --from-literal=BRIGHTDATA_COLLECTOR_ID="${BRIGHTDATA_COLLECTOR_ID}" \
  --from-literal=BRIGHTDATA_ANTHROPIC_COLLECTOR_ID="${BRIGHTDATA_ANTHROPIC_COLLECTOR_ID}" \
  --from-literal=BRIGHTDATA_OPENAI_COLLECTOR_ID="${BRIGHTDATA_OPENAI_COLLECTOR_ID:-}" \
  --dry-run=client -o yaml | kubectl apply -f -

if [[ "${HACKATHON_SKIP_SIGNOZ:-0}" != "1" ]]; then
  "${SCRIPT_DIR}/deploy_signoz.sh"
fi

MINIKUBE_PROFILE_NAME="${MINIKUBE_PROFILE_NAME:-minikube}"
eval "$(minikube -p "${MINIKUBE_PROFILE_NAME}" docker-env --shell bash)"
docker build -t hackathon-backend:local "${SRC_ROOT}/backend"
docker build -t hackathon-frontend:local "${SRC_ROOT}/frontend"

kubectl apply -f "${SCRIPT_DIR}/local.yaml"
kubectl -n hackathon rollout status deployment/hackathon-postgres
kubectl -n hackathon rollout restart deployment/hackathon-backend deployment/hackathon-frontend
kubectl -n hackathon rollout status deployment/hackathon-backend
kubectl -n hackathon exec deployment/hackathon-backend -- \
  env OTEL_SDK_DISABLED=true python manage.py migrate --noinput
kubectl -n hackathon rollout status deployment/hackathon-frontend

echo "Run: kubectl -n hackathon port-forward service/hackathon-frontend 5173:5173"
echo "SigNoz: kubectl -n signoz port-forward service/signoz 8080:8080"
