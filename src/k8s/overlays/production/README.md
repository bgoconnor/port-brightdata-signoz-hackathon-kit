# Future production overlay

Production is intentionally not deployable yet. Create a `kustomization.yaml` here only after the production platform is chosen.

The production overlay must provide:

- immutable backend and frontend images from the production registry;
- `DJANGO_SETTINGS_MODULE=config.settings.production`;
- `DJANGO_SECRET_KEY` and vendor credentials from an external secret manager;
- explicit `DJANGO_ALLOWED_HOSTS` and trusted origins;
- a managed database or an explicitly operated persistent database;
- ingress, DNS, TLS, resource sizing, replicas, and disruption policy;
- an environment-specific namespace that is not `hackathon`.

Never reuse `overlays/local` or its development secret in production.

