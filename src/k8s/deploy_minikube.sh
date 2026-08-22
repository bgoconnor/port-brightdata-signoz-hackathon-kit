#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

minikube image build -t hackathon-backend:local "${SRC_ROOT}/backend"
minikube image build -t hackathon-frontend:local "${SRC_ROOT}/frontend"

kubectl apply -f "${SCRIPT_DIR}/local.yaml"
kubectl -n hackathon rollout status deployment/hackathon-postgres
kubectl -n hackathon rollout restart deployment/hackathon-backend deployment/hackathon-frontend
kubectl -n hackathon rollout status deployment/hackathon-backend
kubectl -n hackathon exec deployment/hackathon-backend -- python manage.py migrate --noinput
kubectl -n hackathon rollout status deployment/hackathon-frontend

echo "Run: kubectl -n hackathon port-forward service/hackathon-frontend 5173:5173"
