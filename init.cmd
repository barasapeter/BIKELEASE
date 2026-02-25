@echo off
setlocal enabledelayedexpansion

set ROOT=bikelease

echo Creating bikelease project structure...

for %%D in (
  "%ROOT%\apps\api\routers"
  "%ROOT%\apps\api\schemas"
  "%ROOT%\apps\api\middleware"
  "%ROOT%\apps\web\templates\rentals"
  "%ROOT%\apps\web\templates\bikes"
  "%ROOT%\apps\web\static\css"
  "%ROOT%\apps\web\static\js"
  "%ROOT%\core"
  "%ROOT%\domain\services"
  "%ROOT%\data\models"
  "%ROOT%\data\repositories"
  "%ROOT%\data\migrations"
  "%ROOT%\integrations\mpesa"
  "%ROOT%\integrations\notifications"
  "%ROOT%\tests\api"
  "%ROOT%\tests\domain"
  "%ROOT%\tests\data"
  "%ROOT%\infra\docker"
  "%ROOT%\infra\terraform\modules"
  "%ROOT%\infra\terraform\envs\dev"
  "%ROOT%\infra\terraform\envs\prod"
  "%ROOT%\scripts"
) do (
  if not exist %%D mkdir %%D
)

:: usage: call :touch <path>
goto :main

:touch
  if not exist "%~1" type nul > "%~1"
  exit /b

:main

for %%F in (
  "%ROOT%\apps\api\__init__.py"
  "%ROOT%\apps\api\routers\__init__.py"
  "%ROOT%\apps\api\schemas\__init__.py"
  "%ROOT%\apps\api\middleware\__init__.py"
  "%ROOT%\apps\web\__init__.py"
  "%ROOT%\core\__init__.py"
  "%ROOT%\domain\__init__.py"
  "%ROOT%\domain\services\__init__.py"
  "%ROOT%\data\__init__.py"
  "%ROOT%\data\models\__init__.py"
  "%ROOT%\data\repositories\__init__.py"
  "%ROOT%\integrations\mpesa\__init__.py"
  "%ROOT%\integrations\notifications\__init__.py"
  "%ROOT%\tests\__init__.py"
  "%ROOT%\tests\api\__init__.py"
  "%ROOT%\tests\domain\__init__.py"
  "%ROOT%\tests\data\__init__.py"
) do (
  call :touch %%F
)

for %%F in (
  "%ROOT%\apps\api\main.py"
  "%ROOT%\apps\api\deps.py"
  "%ROOT%\apps\api\routers\health.py"
  "%ROOT%\apps\api\routers\auth.py"
  "%ROOT%\apps\api\routers\bikes.py"
  "%ROOT%\apps\api\routers\customers.py"
  "%ROOT%\apps\api\routers\rentals.py"
  "%ROOT%\apps\api\routers\payments.py"
  "%ROOT%\apps\api\routers\reports.py"
  "%ROOT%\apps\api\schemas\bike.py"
  "%ROOT%\apps\api\schemas\customer.py"
  "%ROOT%\apps\api\schemas\rental.py"
  "%ROOT%\apps\api\schemas\payment.py"
  "%ROOT%\apps\api\schemas\report.py"
  "%ROOT%\apps\api\middleware\cors.py"
  "%ROOT%\apps\api\middleware\request_id.py"
  "%ROOT%\apps\api\middleware\error_handlers.py"
  "%ROOT%\apps\web\main.py"
  "%ROOT%\apps\web\templates\base.html"
  "%ROOT%\apps\web\templates\dashboard.html"
  "%ROOT%\apps\web\templates\rentals\start.html"
  "%ROOT%\apps\web\templates\rentals\stop.html"
  "%ROOT%\apps\web\templates\bikes\list.html"
  "%ROOT%\core\config.py"
  "%ROOT%\core\logging.py"
  "%ROOT%\core\security.py"
  "%ROOT%\core\errors.py"
  "%ROOT%\domain\models.py"
  "%ROOT%\domain\pricing.py"
  "%ROOT%\domain\policies.py"
  "%ROOT%\domain\services\rental_service.py"
  "%ROOT%\domain\services\payment_service.py"
  "%ROOT%\domain\services\report_service.py"
  "%ROOT%\data\db.py"
  "%ROOT%\data\models\bike.py"
  "%ROOT%\data\models\customer.py"
  "%ROOT%\data\models\rental.py"
  "%ROOT%\data\models\payment.py"
  "%ROOT%\data\repositories\bike_repo.py"
  "%ROOT%\data\repositories\customer_repo.py"
  "%ROOT%\data\repositories\rental_repo.py"
  "%ROOT%\data\repositories\payment_repo.py"
  "%ROOT%\integrations\mpesa\client.py"
  "%ROOT%\integrations\mpesa\schemas.py"
  "%ROOT%\infra\docker\Dockerfile"
  "%ROOT%\infra\docker\docker-compose.yml"
  "%ROOT%\scripts\seed.py"
  "%ROOT%\scripts\create_admin.py"
  "%ROOT%\pyproject.toml"
  "%ROOT%\alembic.ini"
  "%ROOT%\README.md"
) do (
  call :touch %%F
)

echo.
echo Done! Project created at .\%ROOT%
endlocal
