#!/bin/bash
# Project Build Script - Auto-generated
# Technology: Python/pyproject.toml + Docker Compose | Generated: 2026-04-26
# Source repo: E:/MyProject/clinic-cms-workspace/clinic-cms

SOURCE_DIR="E:/MyProject/clinic-cms-workspace/clinic-cms"
ACTION="${1:-build}"

cd "$SOURCE_DIR" || exit 1

case "$ACTION" in
  build)
    python -m build --quiet 2>&1 | tail -5
    ;;
  test)
    docker exec clinic_cms_api pytest -q --tb=short 2>&1 || \
    pytest -q --tb=short 2>&1
    ;;
  test-unit)
    docker exec clinic_cms_api pytest tests/unit/ -q --tb=short 2>&1 || \
    pytest tests/unit/ -q --tb=short 2>&1
    ;;
  lint)
    docker exec clinic_cms_api ruff check app tests 2>&1 || \
    ruff check app tests 2>&1
    ;;
  run)
    docker compose -f docker/docker-compose.yml up -d
    ;;
  clean)
    find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null; echo "cleaned"
    ;;
  install)
    pip install -e ".[dev]" -q
    ;;
  check)
    docker exec clinic_cms_api python -c "import app.main; print('OK')" 2>&1 || \
    python -c "import app.main; print('OK')" 2>&1
    ;;
  migrate)
    docker exec clinic_cms_api alembic upgrade head 2>&1
    ;;
  *)
    echo "Unknown action: $ACTION"
    exit 1
    ;;
esac
