#!/usr/bin/env bash
#
# deploy.sh — pull latest code for both repos and (re)deploy the prod stack.
#
#   ./deploy.sh              # pull + build + up (default)
#   ./deploy.sh --no-pull    # skip git pull, just rebuild + up (use local code)
#   ./deploy.sh --logs       # after deploy, tail api logs
#   ./deploy.sh down         # stop the stack
#
# Requires: docker (with compose v2), git, and a filled ./.env.prod.
set -euo pipefail

cd "$(dirname "$0")"
COMPOSE="docker compose -f docker-compose.prod.yml --env-file .env.prod"

# ── Preconditions ────────────────────────────────────────────────────────────
if [ ! -f .env.prod ]; then
  echo "ERROR: .env.prod not found. Create it first:"
  echo "       cp .env.prod.example .env.prod && \$EDITOR .env.prod"
  exit 1
fi
command -v docker >/dev/null || { echo "ERROR: docker not installed"; exit 1; }
docker compose version >/dev/null 2>&1 || { echo "ERROR: docker compose v2 required"; exit 1; }

# Load deploy-time vars (repo URLs, branch) from .env.prod.
set -a; . ./.env.prod; set +a
BE_REPO="${BE_REPO:-git@github.com:chien0661/medizen-clinic-be.git}"
FE_REPO="${FE_REPO:-git@github.com:chien0661/medizen-clinic-web.git}"
BRANCH="${DEPLOY_BRANCH:-main}"

# ── Subcommands ──────────────────────────────────────────────────────────────
case "${1:-up}" in
  down)   echo "Stopping stack..."; $COMPOSE down; exit 0 ;;
  --logs) DO_LOGS=1 ;;
  --no-pull) NO_PULL=1 ;;
esac

# ── 1. Sync source repos ─────────────────────────────────────────────────────
sync_repo() {
  local dir="$1" url="$2"
  if [ -d "$dir/.git" ]; then
    echo "  → updating $dir ($BRANCH)"
    git -C "$dir" fetch --depth 1 origin "$BRANCH"
    git -C "$dir" checkout -q "$BRANCH"
    git -C "$dir" reset --hard "origin/$BRANCH"
  else
    echo "  → cloning $url → $dir"
    git clone --depth 1 -b "$BRANCH" "$url" "$dir"
  fi
}

if [ "${NO_PULL:-0}" != "1" ]; then
  echo "[1/4] Syncing source repos..."
  sync_repo repos/backend  "$BE_REPO"
  sync_repo repos/frontend "$FE_REPO"
else
  echo "[1/4] --no-pull: using existing repos/ code"
fi

# ── 2. Stage the web prod Dockerfile + nginx into the frontend build context ──
echo "[2/4] Staging web build files..."
cp web/Dockerfile.prod repos/frontend/Dockerfile.prod
cp web/nginx.conf       repos/frontend/nginx.conf

# ── 3. Build images ──────────────────────────────────────────────────────────
echo "[3/4] Building images..."
$COMPOSE build

# ── 4. Bring the stack up ────────────────────────────────────────────────────
echo "[4/4] Starting stack..."
$COMPOSE up -d

# ── Health wait (api migrates on boot) ───────────────────────────────────────
echo "Waiting for API to become healthy..."
API_PORT="${API_PORT:-8000}"
for i in $(seq 1 60); do
  if curl -fsS "http://127.0.0.1:${API_PORT}/health" >/dev/null 2>&1; then
    echo "  API healthy."
    break
  fi
  [ "$i" = "60" ] && { echo "  WARN: API not healthy after 120s — check: $COMPOSE logs api"; }
  sleep 2
done

echo ""
echo "======================================================"
echo " Deploy complete."
echo "   Web:  http://<host>:${WEB_PORT:-80}"
echo "   API:  http://127.0.0.1:${API_PORT} (localhost only)"
echo "   Logs: $COMPOSE logs -f api"
echo "======================================================"
$COMPOSE ps

[ "${DO_LOGS:-0}" = "1" ] && $COMPOSE logs -f api
