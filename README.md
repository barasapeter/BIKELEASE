# Another Cloud-Native Backend Engineering Marvel
## Bike Lease Tracking Tool for Local Businesses
This is an enterprise-level API-driven lease tracking tool built on top of FastAPI, conteinerized with docker. The infrastructure provisioning and deployment is done entirely with terraform.

## Initial Project Structure
```
bikelease/
├─ apps/
│  ├─ api/
│  │  ├─ main.py
│  │  ├─ deps.py
│  │  ├─ routers/
│  │  │  ├─ health.py
│  │  │  ├─ auth.py
│  │  │  ├─ bikes.py
│  │  │  ├─ customers.py
│  │  │  ├─ rentals.py
│  │  │  ├─ payments.py
│  │  │  └─ reports.py
│  │  ├─ schemas/              # pydantic DTOs
│  │  │  ├─ bike.py
│  │  │  ├─ customer.py
│  │  │  ├─ rental.py
│  │  │  ├─ payment.py
│  │  │  └─ report.py
│  │  └─ middleware/
│  │     ├─ cors.py
│  │     ├─ request_id.py
│  │     └─ error_handlers.py
│  │
│  └─ web/                      # thin client
│     ├─ main.py                # mount   service
│     ├─ templates/
│     │  ├─ base.html
│     │  ├─ dashboard.html
│     │  ├─ rentals/
│     │  │  ├─ start.html
│     │  │  └─ stop.html
│     │  └─ bikes/
│     │     └─ list.html
│     └─ static/
│        ├─ css/
│        └─ js/
│
├─ core/
│  ├─ config.py                 # pydantic-settings
│  ├─ logging.py                # structlogloguru setup
│  ├─ security.py               # password hashing JWT utils
│  └─ errors.py                 # custom exceptions
│
├─ domain/                      # business rules, pure-ish Python
│  ├─ models.py                 # dataclasses  domain objects 
│  ├─ pricing.py                # compute rental cost, penalties
│  ├─ services/
│  │  ├─ rental_service.py      # start Or stop rental, state transitions
│  │  ├─ payment_service.py     # recordverify payment, receipts
│  │  └─ report_service.py      # daily revenue utilization
│  └─ policies.py               # rules: overdue, collateral, etc.
│
├─ data/
│  ├─ db.py                     # enginesession
│  ├─ models/                   # SQLAlchemy ORM models
│  │  ├─ bike.py
│  │  ├─ customer.py
│  │  ├─ rental.py
│  │  └─ payment.py
│  ├─ repositories/             # data access layer
│  │  ├─ bike_repo.py
│  │  ├─ customer_repo.py
│  │  ├─ rental_repo.py
│  │  └─ payment_repo.py
│  └─ migrations/               # alembic
│
├─ integrations/
│  ├─ mpesa/                    # STK push, callbacks
│  │  ├─ client.py
│  │  └─ schemas.py
│  └─ notifications/            # sms email whatsapp
│
├─ tests/
│  ├─ api/
│  ├─ domain/
│  └─ data/
│
├─ infra/
│  ├─ docker/
│  │  ├─ Dockerfile
│  │  └─ docker-compose.yml
│  └─ terraform/
│     ├─ modules/
│     └─ envs/
│        ├─ dev/
│        └─ prod/
│
├─ scripts/
│  ├─ seed.py
│  └─ create_admin.py
│
├─ pyproject.toml
├─ alembic.ini
└─ README.md
```

Run the app with `uvicorn apps.api.main:app --reload` in development.
