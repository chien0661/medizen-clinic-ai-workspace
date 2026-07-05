# MediZen Clinic CMS — Production Deploy

Self-contained deploy toolkit that lives **outside** the source repos. It pulls
the backend + frontend from GitHub and runs the full stack with Docker Compose.

```
deploy/
├── docker-compose.prod.yml   # postgres + redis + api + worker + web (nginx)
├── deploy.sh                 # pull code → build → up (+ health check)
├── .env.prod.example         # copy → .env.prod and fill secrets
├── web/
│   ├── Dockerfile.prod       # builds the web SPA, serves via nginx
│   └── nginx.conf            # SPA + reverse-proxy /api → api service
└── repos/                    # (auto) cloned backend/ and frontend/ — gitignored
```

## First-time setup (on the prod server)

```bash
# 1. Copy this deploy/ folder to the server (git, scp, rsync…)
# 2. Configure secrets
cp .env.prod.example .env.prod
$EDITOR .env.prod            # set JWT_SECRET, POSTGRES_PASSWORD, KMS/Vault, etc.
# 3. Make sure the server can `git clone` both repos (SSH deploy key or HTTPS token)
# 4. Deploy
./deploy.sh
```

`deploy.sh` clones/updates both repos into `repos/`, builds images, and starts
the stack. The API runs Alembic migrations and seeds the superadmin on boot
(idempotent — **no demo data** in production).

## Everyday operations

```bash
./deploy.sh                 # pull latest main + rebuild + restart
./deploy.sh --no-pull       # rebuild from current local code only
./deploy.sh --logs          # deploy then tail API logs
./deploy.sh down            # stop the stack

docker compose -f docker-compose.prod.yml --env-file .env.prod ps
docker compose -f docker-compose.prod.yml --env-file .env.prod logs -f api
```

## Notes

- **TLS**: the `web` service listens on plain HTTP (port `WEB_PORT`, default 80).
  Terminate HTTPS in front of it (Caddy / Traefik / cloud load balancer).
- **KMS**: production must set `KMS_PROVIDER=vault` (see `.env.prod`). `local-dev`
  is not safe for real patient PII.
- **API** is published on `127.0.0.1:${API_PORT}` (localhost only); the browser
  reaches it through nginx at `/api`.
- **Backups**: the `pgdata` / `redisdata` named volumes hold all state — include
  them in your backup routine.
- Deploy branch defaults to `main`; override `DEPLOY_BRANCH` / `BE_REPO` /
  `FE_REPO` in `.env.prod`.
