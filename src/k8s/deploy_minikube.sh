#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
LOCAL_OVERLAY="${SCRIPT_DIR}/overlays/local"
NAMESPACE="hackathon"
BACKEND_IMAGE="hackathon-backend:local"
FRONTEND_IMAGE="hackathon-frontend:local"
LOCAL_PORT="${HACKATHON_LOCAL_PORT:-18080}"
SKIP_PORT_FORWARD="${HACKATHON_SKIP_PORT_FORWARD:-0}"

for command_name in minikube kubectl curl; do
    if ! command -v "${command_name}" >/dev/null 2>&1; then
        echo "Required command not found: ${command_name}" >&2
        exit 1
    fi
done

if [[ "$(kubectl config current-context)" != "minikube" ]]; then
    echo "Refusing to deploy: kubectl context is not minikube." >&2
    exit 1
fi

if ! minikube status >/dev/null 2>&1; then
    echo "Refusing to deploy: minikube is not running." >&2
    exit 1
fi

echo "Building backend image inside Minikube..."
minikube image build --tag "${BACKEND_IMAGE}" "${SRC_ROOT}/backend"

echo "Building frontend image inside Minikube..."
minikube image build --tag "${FRONTEND_IMAGE}" "${SRC_ROOT}/frontend"

echo "Applying the local Kubernetes overlay..."
kubectl apply -k "${LOCAL_OVERLAY}"

echo "Restarting deployments so the rebuilt local tags are used..."
kubectl -n "${NAMESPACE}" rollout restart \
    deployment/hackathon-backend \
    deployment/hackathon-frontend

kubectl -n "${NAMESPACE}" rollout status deployment/hackathon-backend --timeout=180s
kubectl -n "${NAMESPACE}" rollout status deployment/hackathon-frontend --timeout=180s

kubectl -n "${NAMESPACE}" get deployments,pods,services

if [[ "${SKIP_PORT_FORWARD}" == "1" ]]; then
    echo "Deployment complete. Port forwarding was skipped."
    echo "Run: kubectl -n ${NAMESPACE} port-forward service/hackathon-frontend ${LOCAL_PORT}:80"
    exit 0
fi

if command -v lsof >/dev/null 2>&1 && \
    lsof -nP -iTCP:"${LOCAL_PORT}" -sTCP:LISTEN >/dev/null 2>&1; then
    echo "Local port ${LOCAL_PORT} is already in use; refusing to replace its listener." >&2
    exit 1
fi

echo "Forwarding http://127.0.0.1:${LOCAL_PORT} to the frontend service..."
kubectl -n "${NAMESPACE}" port-forward \
    service/hackathon-frontend "${LOCAL_PORT}:80" &
FORWARD_PID=$!

cleanup() {
    if kill -0 "${FORWARD_PID}" >/dev/null 2>&1; then
        kill "${FORWARD_PID}" >/dev/null 2>&1 || true
        wait "${FORWARD_PID}" 2>/dev/null || true
    fi
}
trap cleanup EXIT INT TERM

for attempt in $(seq 1 30); do
    if curl --fail --silent --show-error \
        "http://127.0.0.1:${LOCAL_PORT}/healthz" >/dev/null; then
        break
    fi
    if ! kill -0 "${FORWARD_PID}" >/dev/null 2>&1; then
        echo "Port-forward stopped before the frontend became reachable." >&2
        exit 1
    fi
    if [[ "${attempt}" == "30" ]]; then
        echo "Frontend did not become reachable through the port-forward." >&2
        exit 1
    fi
    sleep 1
done

curl --fail --silent --show-error "http://127.0.0.1:${LOCAL_PORT}/" >/dev/null
curl --fail --silent --show-error "http://127.0.0.1:${LOCAL_PORT}/api/health/" >/dev/null

echo "Verified frontend and Django API through http://127.0.0.1:${LOCAL_PORT}"
echo "Press Ctrl-C to stop port forwarding."
wait "${FORWARD_PID}"
