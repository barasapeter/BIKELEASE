# BIKELEASE

BIKELEASE is a FastAPI-based bike rental operations platform for small and medium lease shops. It combines:
- a server-rendered web app (Jinja2 + vanilla JS),
- API endpoints for auth, fleet, customers, sessions, checkout, and reports,
- PostgreSQL persistence through SQLAlchemy,
- M-Pesa STK Push integration for digital checkout.

The app is designed around **minute-based bike leasing**: start a session, track duration, stop it, and settle with cash or M-Pesa.

---

## What this repository currently contains

This codebase includes both production-use code and scaffold placeholders generated from `init.sh` / `init.cmd`.

- **Implemented and active** modules: `apps/api/main.py`, `apps/web/main.py`, API routers (`auth`, `shop`, `bikes`, `customers`, `payments`, `queries`), ORM models, auth/security, utility helpers, templates, and static assets.
- **Placeholder/empty files** exist for some planned layers (`domain/services/*`, `apps/api/schemas/*`, `apps/api/routers/health.py`, `reports.py`, etc.).

This README reflects the code as it exists now.

---

## Product flow

1. A shop owner creates an account and shops.
2. Owner creates employees and bikes.
3. Staff creates/fetches a customer.
4. Staff starts a bike session.
5. Session runs until stopped.
6. Checkout is processed as:
   - `CASH`, or
   - `MPESA` (STK Push + callback webhook).
7. Sessions are visible in shop views and query endpoints.

---

## Tech stack

### Backend
- **Python**
- **FastAPI** for routing and web server integration
- **Uvicorn/Gunicorn** runtime dependencies
- **SQLAlchemy 2.x style ORM** (`DeclarativeBase`, typed `Mapped[]`)
- **PostgreSQL-specific types** (`JSONB`, `UUID`) in models
- **Pydantic Settings** for environment configuration
- **Passlib + JOSE JWT** for PIN hashing and cookie token auth

### Frontend
- **Jinja2 templates** (server-rendered pages)
- **Vanilla JavaScript** for UX/workflow interactions
- **Custom CSS** theme system (dark/light in landing page)
- **SweetAlert2** used on workflow screens for toasts/dialogs

### Integrations
- **Safaricom M-Pesa STK Push** via async `httpx` calls

### Tooling / operations
- **Alembic** is present (config + env), but migrations are not fully built out in this repo state.
- **Docker files exist but are currently empty placeholders**.
- **Pytest tests exist**, focused on auth flow and utility functions.

---

## Architecture and layout

```text
apps/
  api/
    main.py                 # FastAPI app factory, router mounting, static mount, DB init
    routers/
      auth.py               # owner/employee auth + cookies
      shop.py               # shop creation
      bikes.py              # bike creation/update
      customers.py          # customer, start/stop session, checkout
      payments.py           # M-Pesa callback webhook
      queries.py            # session listing query
      health.py             # placeholder
      rentals.py            # placeholder
      reports.py            # placeholder
  web/
    main.py                 # page routes + template rendering
    templates/              # Jinja HTML pages
    static/                 # CSS, JS, images

core/
  config.py                 # env settings contract
  security.py               # JWT + cookie auth + user resolution
  errors.py                 # custom exceptions

data/
  db.py                     # SQLAlchemy engine + session dependency
  models/__init__.py        # ORM entities + enums
  repositories/             # placeholders

integrations/
  mpesa/
    client.py               # token + STK push initiation

scripts/
  create_admin.py           # bootstrap owner account
  seed.py                   # local/dev seed data
  simulate_btoc.py          # callback simulation helper
  simulate_ctob.py          # callback simulation helper

tests/
  test_auth_v1.py
  test_utils.py
```

---

## Key web pages (including `lander.html`)

The homepage template is `apps/web/templates/lander.html` and presents BIKELEASE as a leasing + tracking + payments product with:
- hero messaging,
- “How it works” flow,
- USSD positioning,
- payment capability highlights,
- login CTA to `/login`.

Additional pages include dashboard, shop overview, bikes list/create, session list, session details, start/stop and checkout interfaces.

---

## API surface (active)

Base prefixes are mounted in `apps/api/main.py`.

### Auth (`/auth/v1`)
- `POST /create-shop-owner`
- `POST /create-employee`
- `POST /login`
- `POST /logout`

### Shops (`/shop/v1`)
- `POST /create-shop`

### Bikes (`/bikes/v1`)
- `POST /create-bike`
- `PATCH /update`

### Customers + sessions + checkout (`/customers/v1`)
- `POST /create-customer`
- `POST /start-session`
- `PATCH /stop-session`
- `POST /checkout-session`

### Payments (`/payments/v1`)
- `POST /hook` (M-Pesa callback receiver)

### Queries (`/queries/v1`)
- `GET /sessions/{shop_id}/all`

---

## Data model (implemented)

Primary SQLAlchemy entities are defined in `data/models/__init__.py`:
- `ShopOwner`
- `Shop`
- `Employee`
- `Customer`
- `Bike`
- `Session`
- `SessionCheckout`
- `MpesaCheckout`

Enums:
- `PaymentMethod`: `CASH`, `MPESA`
- `MpesaTransactionStatus`: `PENDING`, `SUCCESS`, `FAILED`, `CANCELLED`

Notable model behavior:
- Session checkout is one-to-one with session.
- M-Pesa checkout is one-to-one with session checkout.
- Flexible metadata is stored with `JSONB` fields (`metadata_e`) across entities.

---

## Authentication and authorization

- Login is PIN-based and category-based (`owner` or `employee`).
- Access and refresh JWTs are issued as HTTP-only cookies.
- CSRF token cookie is also set; helper exists for header-vs-cookie comparison.
- Protected endpoints resolve current user through cookie token payload and DB lookup.

Authorization logic is route-level and role-aware:
- owners can act within owned shops,
- employees are scoped to their assigned shop.

---

## Configuration

Environment variables are declared in `core/config.py` via `GlobalSettings`.

Required values:
- `DATABASE_URL`
- `TEST_DATABASE_URL`
- `JWT_SECRET_KEY`
- `APP_NAME`
- `C2B_CONSUMER_KEY`
- `C2B_CONSUMER_SECRET`
- `C2B_SHORTCODE`
- `C2B_ONLINE_PASSKEY`
- `B2C_CONSUMER_KEY`
- `B2C_CONSUMER_SECRET`
- `B2C_SHORTCODE`
- `B2C_INITIATOR_NAME`
- `B2C_SECURITY_CREDENTIAL`

Create a local `.env` file at repository root with these keys.

---

## Running locally

### 1) Install dependencies
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2) Configure `.env`
Set all keys listed above.

### 3) Start application
```bash
uvicorn apps.api.main:app --reload
```

The web UI is served from the same app (template routes under `/`).

---

## Testing

Run tests with:

```bash
pytest -q
```

Current tests include:
- auth endpoint behavior (`tests/test_auth_v1.py`)
- phone number normalization/validation helpers (`tests/test_utils.py`)

> Note: tests require a valid environment and reachable database because app settings and DB engine are initialized from environment-backed config.

---

## Current gaps and cleanup opportunities

1. Several files are scaffolds/placeholders and should either be implemented or removed to reduce confusion.
2. `pyproject.toml`, Dockerfile, and compose file are empty in this snapshot.
3. Some route logic and naming can be hardened/refactored (validation consistency, error detail handling, function naming cleanup, stricter typing).
4. API docs are disabled in FastAPI app config (`docs_url=None`, `redoc_url=None`, `openapi_url=None`); enable in non-production contexts if needed.
5. Add migration scripts and stronger CI checks to align with the data model lifecycle.

---

## Suggested next milestones

- Add complete Alembic revision history.
- Fill domain/services and schema layers, then wire routers to typed DTOs.
- Restore containerization assets (`infra/docker/*`) and document a one-command local stack.
- Add integration tests for full rental flow (create customer → start → stop → checkout).
- Add structured logging and request-id middleware wiring in app startup.

---

## License

No explicit license file is present in this repository snapshot.
