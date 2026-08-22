# Paper Factory application

This directory contains the runnable hackathon application:

- `backend/` — Django API served by Gunicorn;
- `frontend/` — React/Vite build served by Nginx, with `/api/` proxied to Django;
- `k8s/` — shared Kubernetes resources and environment overlays.

## Local development without Kubernetes

Backend:

```bash
cd src/backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver 127.0.0.1:8000
```

Frontend, in another terminal:

```bash
cd src/frontend
npm install
npm run dev
```

Vite proxies `/api` to the local Django server. The Minikube deployment uses Nginx for the same-origin proxy instead.

