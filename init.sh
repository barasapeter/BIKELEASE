#!/usr/bin/env bash
set -euo pipefail

ROOT="bikelease"

echo "Creating bikelease project structure..."

dirs=(
  "$ROOT/apps/api/routers"
  "$ROOT/apps/api/schemas"
  "$ROOT/apps/api/middleware"
  "$ROOT/apps/web/templates/rentals"
  "$ROOT/apps/web/templates/bikes"
  "$ROOT/apps/web/static/css"
  "$ROOT/apps/web/static/js"
  "$ROOT/core"
  "$ROOT/domain/services"
  "$ROOT/data/models"
  "$ROOT/data/repositories"
  "$ROOT/data/migrations"
  "$ROOT/integrations/mpesa"
  "$ROOT/integrations/notifications"
  "$ROOT/tests/api"
  "$ROOT/tests/domain"
  "$ROOT/tests/data"
  "$ROOT/infra/docker"
  "$ROOT/infra/terraform/modules"
  "$ROOT/infra/terraform/envs/dev"
  "$ROOT/infra/terraform/envs/prod"
  "$ROOT/scripts"
)

for d in "${dirs[@]}"; do
  mkdir -p "$d"
done

touch_file() { [ -f "$1" ] || touch "$1"; }

init_pkg() {
  for dir in "$@"; do
    touch_file "$dir/__init__.py"
  done
}

init_pkg \
  "$ROOT/apps/api" \
  "$ROOT/apps/api/routers" \
  "$ROOT/apps/api/schemas" \
  "$ROOT/apps/api/middleware" \
  "$ROOT/apps/web" \
  "$ROOT/core" \
  "$ROOT/domain" \
  "$ROOT/domain/services" \
  "$ROOT/data" \
  "$ROOT/data/models" \
  "$ROOT/data/repositories" \
  "$ROOT/integrations/mpesa" \
  "$ROOT/integrations/notifications" \
  "$ROOT/tests" \
  "$ROOT/tests/api" \
  "$ROOT/tests/domain" \
  "$ROOT/tests/data"

files=(
  # api
  "$ROOT/apps/api/main.py"
  "$ROOT/apps/api/deps.py"
  "$ROOT/apps/api/routers/health.py"
  "$ROOT/apps/api/routers/auth.py"
  "$ROOT/apps/api/routers/bikes.py"
  "$ROOT/apps/api/routers/customers.py"
  "$ROOT/apps/api/routers/rentals.py"
  "$ROOT/apps/api/routers/payments.py"
  "$ROOT/apps/api/routers/reports.py"
  "$ROOT/apps/api/schemas/bike.py"
  "$ROOT/apps/api/schemas/customer.py"
  "$ROOT/apps/api/schemas/rental.py"
  "$ROOT/apps/api/schemas/payment.py"
  "$ROOT/apps/api/schemas/report.py"
  "$ROOT/apps/api/middleware/cors.py"
  "$ROOT/apps/api/middleware/request_id.py"
  "$ROOT/apps/api/middleware/error_handlers.py"
  # web
  "$ROOT/apps/web/main.py"
  "$ROOT/apps/web/templates/base.html"
  "$ROOT/apps/web/templates/dashboard.html"
  "$ROOT/apps/web/templates/rentals/start.html"
  "$ROOT/apps/web/templates/rentals/stop.html"
  "$ROOT/apps/web/templates/bikes/list.html"
  # core
  "$ROOT/core/config.py"
  "$ROOT/core/logging.py"
  "$ROOT/core/security.py"
  "$ROOT/core/errors.py"
  # domain
  "$ROOT/domain/models.py"
  "$ROOT/domain/pricing.py"
  "$ROOT/domain/policies.py"
  "$ROOT/domain/services/rental_service.py"
  "$ROOT/domain/services/payment_service.py"
  "$ROOT/domain/services/report_service.py"
  # data
  "$ROOT/data/db.py"
  "$ROOT/data/models/bike.py"
  "$ROOT/data/models/customer.py"
  "$ROOT/data/models/rental.py"
  "$ROOT/data/models/payment.py"
  "$ROOT/data/repositories/bike_repo.py"
  "$ROOT/data/repositories/customer_repo.py"
  "$ROOT/data/repositories/rental_repo.py"
  "$ROOT/data/repositories/payment_repo.py"
  # integrations
  "$ROOT/integrations/mpesa/client.py"
  "$ROOT/integrations/mpesa/schemas.py"
  # infra
  "$ROOT/infra/docker/Dockerfile"
  "$ROOT/infra/docker/docker-compose.yml"
  # scripts
  "$ROOT/scripts/seed.py"
  "$ROOT/scripts/create_admin.py"
  # root
  "$ROOT/pyproject.toml"
  "$ROOT/alembic.ini"
  "$ROOT/README.md"
)

for f in "${files[@]}"; do
  touch_file "$f"
done

echo "created at ./$ROOT"
