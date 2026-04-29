from __future__ import annotations

import uuid
import logging
from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from data.db import get_db
from data.models import (
    Bike,
    Customer,
    Employee,
    MpesaTransactionStatus,
    PaymentMethod,
    Session as RentalSession,
    SessionCheckout,
    Shop,
    ShopOwner,
)
from core import config
from core.security import get_current_user

router = APIRouter()

SETTINGS = config.GlobalSettings()
logger = logging.getLogger(SETTINGS.APP_NAME)


def _utc_now() -> datetime:
    return datetime.now(tz=timezone.utc)


def _resolve_shop_or_403(
    shop_id: uuid.UUID,
    current_user: ShopOwner | Employee,
    db: Session,
) -> Shop:
    shop: Shop | None = db.get(Shop, shop_id)
    if shop is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Shop '{shop_id}' not found.",
        )
    
    if isinstance(current_user, ShopOwner):
        if shop.owner_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not own this shop.",
            )
    elif isinstance(current_user, Employee):
        if current_user.shop_id != shop_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not an employee of this shop.",
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Unrecognised user type.",
        )

    return shop


def _successful_checkout_query(db: Session, shop_id: uuid.UUID):
    return (
        db.query(RentalSession, SessionCheckout)
        .join(SessionCheckout, SessionCheckout.session_id == RentalSession.id)
        .join(Bike, Bike.id == RentalSession.bike_id)
        # Only include completed M-Pesa payments (cash checkouts have no MpesaCheckout row)
        .outerjoin(
            "checkout",  # SessionCheckout.mpesa relationship alias
        )
        .filter(Bike.shop_id == shop_id)
        # Exclude sessions whose M-Pesa payment failed or was cancelled
        # (cash sessions will have no mpesa row, so the IS NULL branch keeps them)
    )


@router.get("/daily-revenue")
async def daily_revenue_report(
    shop_id: Annotated[uuid.UUID, Query(description="UUID of the shop to report on")],
    report_date: Annotated[
        datetime | None,
        Query(description="Date to report on (UTC). Defaults to today."),
    ] = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    _resolve_shop_or_403(shop_id, current_user, db)

    target_date: datetime = (report_date or _utc_now()).replace(
        hour=0, minute=0, second=0, microsecond=0, tzinfo=timezone.utc
    )
    next_day = target_date + timedelta(days=1)

    base = (
        db.query(RentalSession, SessionCheckout)
        .join(SessionCheckout, SessionCheckout.session_id == RentalSession.id)
        .join(Bike, Bike.id == RentalSession.bike_id)
        .filter(
            Bike.shop_id == shop_id,
            SessionCheckout.datetime >= target_date,
            SessionCheckout.datetime < next_day,
        )
    )

    rows = base.all()
    total_revenue = sum(float(co.amount_paid) for _, co in rows)
    total_rentals = len(rows)

    by_payment: dict[str, float] = {}
    for _, co in rows:
        method = co.payment_method_enum.value
        by_payment[method] = by_payment.get(method, 0.0) + float(co.amount_paid)

    by_bike: dict[str, dict] = {}
    for session, co in rows:
        bid = session.bike_id
        if bid not in by_bike:
            by_bike[bid] = {"bike_id": bid, "rentals": 0, "revenue": 0.0}
        by_bike[bid]["rentals"] += 1
        by_bike[bid]["revenue"] += float(co.amount_paid)

    return {
        "shop_id": str(shop_id),
        "report_date": target_date.date().isoformat(),
        "total_revenue": round(total_revenue, 2),
        "total_rentals": total_rentals,
        "revenue_by_payment_method": by_payment,
        "revenue_by_bike": sorted(
            by_bike.values(), key=lambda x: x["revenue"], reverse=True
        ),
    }


@router.get("/weekly-revenue")
async def weekly_revenue_report(
    shop_id: Annotated[uuid.UUID, Query(description="UUID of the shop to report on")],
    week_start: Annotated[
        datetime | None,
        Query(
            description=(
                "Start of the 7-day window (UTC, inclusive). "
                "Defaults to the Monday of the current week."
            )
        ),
    ] = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    _resolve_shop_or_403(shop_id, current_user, db)

    now = _utc_now()
    if week_start is None:
        # Default: Monday 00:00 UTC of the current week
        week_start = (now - timedelta(days=now.weekday())).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
    else:
        week_start = week_start.replace(
            hour=0, minute=0, second=0, microsecond=0, tzinfo=timezone.utc
        )
    week_end = week_start + timedelta(days=7)

    rows = (
        db.query(RentalSession, SessionCheckout)
        .join(SessionCheckout, SessionCheckout.session_id == RentalSession.id)
        .join(Bike, Bike.id == RentalSession.bike_id)
        .filter(
            Bike.shop_id == shop_id,
            SessionCheckout.datetime >= week_start,
            SessionCheckout.datetime < week_end,
        )
        .all()
    )

    total_revenue = sum(float(co.amount_paid) for _, co in rows)

    daily: dict[str, float] = {}
    for _, co in rows:
        day_key = co.datetime.date().isoformat()
        daily[day_key] = daily.get(day_key, 0.0) + float(co.amount_paid)

    by_bike: dict[str, dict] = {}
    for session, co in rows:
        bid = session.bike_id
        if bid not in by_bike:
            by_bike[bid] = {
                "bike_id": bid,
                "rentals": 0,
                "revenue": 0.0,
                "total_minutes": 0,
            }
        by_bike[bid]["rentals"] += 1
        by_bike[bid]["revenue"] += float(co.amount_paid)
        by_bike[bid]["total_minutes"] += co.duration_in_minutes

    top_bikes = sorted(by_bike.values(), key=lambda x: x["revenue"], reverse=True)[:5]

    return {
        "shop_id": str(shop_id),
        "week_start": week_start.date().isoformat(),
        "week_end": (week_end - timedelta(days=1)).date().isoformat(),
        "total_revenue": round(total_revenue, 2),
        "total_rentals": len(rows),
        "daily_revenue": dict(sorted(daily.items())),
        "revenue_by_bike": sorted(
            by_bike.values(), key=lambda x: x["revenue"], reverse=True
        ),
        "top_5_profitable_bikes": top_bikes,
    }


@router.get("/bike-utilization")
async def bike_utilization_report(
    shop_id: Annotated[uuid.UUID, Query(description="UUID of the shop to report on")],
    since: Annotated[
        datetime | None,
        Query(
            description="Start of the reporting window (UTC). Defaults to 30 days ago."
        ),
    ] = None,
    until: Annotated[
        datetime | None,
        Query(description="End of the reporting window (UTC). Defaults to now."),
    ] = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):

    _resolve_shop_or_403(shop_id, current_user, db)

    now = _utc_now()
    since = since or (now - timedelta(days=30))
    until = until or now

    bikes: list[Bike] = db.query(Bike).filter(Bike.shop_id == shop_id).all()

    rows = (
        db.query(RentalSession, SessionCheckout)
        .join(SessionCheckout, SessionCheckout.session_id == RentalSession.id)
        .join(Bike, Bike.id == RentalSession.bike_id)
        .filter(
            Bike.shop_id == shop_id,
            SessionCheckout.datetime >= since,
            SessionCheckout.datetime < until,
        )
        .all()
    )

    utilization: dict[str, dict] = {
        b.id: {
            "bike_id": b.id,
            "nickname": b.nickname,
            "rate_per_minute": float(b.rate_per_minute),
            "total_rentals": 0,
            "total_minutes": 0,
            "total_revenue": 0.0,
        }
        for b in bikes
    }

    for session, co in rows:
        bid = session.bike_id
        if bid in utilization:
            utilization[bid]["total_rentals"] += 1
            utilization[bid]["total_minutes"] += co.duration_in_minutes
            utilization[bid]["total_revenue"] += float(co.amount_paid)

    result = []
    for entry in utilization.values():
        rentals = entry["total_rentals"]
        entry["total_hours"] = round(entry["total_minutes"] / 60, 2)
        entry["avg_session_minutes"] = (
            round(entry["total_minutes"] / rentals, 1) if rentals else 0
        )
        entry["total_revenue"] = round(entry["total_revenue"], 2)
        result.append(entry)

    return {
        "shop_id": str(shop_id),
        "since": since.isoformat(),
        "until": until.isoformat(),
        "bikes": sorted(result, key=lambda x: x["total_revenue"], reverse=True),
    }


@router.get("/idle-bikes")
async def idle_bikes_report(
    shop_id: Annotated[uuid.UUID, Query(description="UUID of the shop to report on")],
    idle_threshold_hours: Annotated[
        int,
        Query(
            ge=1,
            description=(
                "A bike is considered idle if its last completed session ended "
                "more than this many hours ago (or it has never been rented). "
                "Defaults to 24."
            ),
        ),
    ] = 24,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    _resolve_shop_or_403(shop_id, current_user, db)

    cutoff = _utc_now() - timedelta(hours=idle_threshold_hours)

    bikes: list[Bike] = db.query(Bike).filter(Bike.shop_id == shop_id).all()

    latest_checkout: dict[str, datetime] = {}
    for bike in bikes:
        last = (
            db.query(func.max(SessionCheckout.datetime))
            .join(RentalSession, RentalSession.id == SessionCheckout.session_id)
            .filter(RentalSession.bike_id == bike.id)
            .scalar()
        )
        if last is not None:
            latest_checkout[bike.id] = last

    idle = []
    for bike in bikes:
        last_activity = latest_checkout.get(bike.id)
        is_idle = last_activity is None or last_activity < cutoff
        if is_idle:
            idle.append(
                {
                    "bike_id": bike.id,
                    "nickname": bike.nickname,
                    "rate_per_minute": float(bike.rate_per_minute),
                    "last_checkout_at": (
                        last_activity.isoformat() if last_activity else None
                    ),
                    "hours_since_last_activity": (
                        round((_utc_now() - last_activity).total_seconds() / 3600, 1)
                        if last_activity
                        else None
                    ),
                    "never_rented": last_activity is None,
                }
            )

    return {
        "shop_id": str(shop_id),
        "idle_threshold_hours": idle_threshold_hours,
        "checked_at": _utc_now().isoformat(),
        "idle_bike_count": len(idle),
        "idle_bikes": sorted(
            idle,
            key=lambda x: (
                x["hours_since_last_activity"] is None,
                -(x["hours_since_last_activity"] or 0),
            ),
        ),
    }


@router.get("/top-customers")
async def top_customers_report(
    shop_id: Annotated[uuid.UUID, Query(description="UUID of the shop to report on")],
    since: Annotated[
        datetime | None,
        Query(
            description="Start of the reporting window (UTC). Defaults to 30 days ago."
        ),
    ] = None,
    until: Annotated[
        datetime | None,
        Query(description="End of the reporting window (UTC). Defaults to now."),
    ] = None,
    limit: Annotated[
        int,
        Query(
            ge=1,
            le=100,
            description="Maximum number of customers to return (default 20).",
        ),
    ] = 20,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):

    _resolve_shop_or_403(shop_id, current_user, db)

    now = _utc_now()
    since = since or (now - timedelta(days=30))
    until = until or now

    rows = (
        db.query(RentalSession, SessionCheckout, Customer)
        .join(SessionCheckout, SessionCheckout.session_id == RentalSession.id)
        .join(Bike, Bike.id == RentalSession.bike_id)
        .join(Customer, Customer.id == RentalSession.customer_id)
        .filter(
            Bike.shop_id == shop_id,
            SessionCheckout.datetime >= since,
            SessionCheckout.datetime < until,
        )
        .all()
    )

    customer_stats: dict[str, dict] = {}
    for session, co, customer in rows:
        cid = str(customer.id)
        if cid not in customer_stats:
            customer_stats[cid] = {
                "customer_id": cid,
                "name": customer.name,
                "primary_phone": customer.primary_phone,
                "total_rentals": 0,
                "total_spent": 0.0,
                "total_minutes": 0,
                "last_visit": None,
            }
        stats = customer_stats[cid]
        stats["total_rentals"] += 1
        stats["total_spent"] += float(co.amount_paid)
        stats["total_minutes"] += co.duration_in_minutes

        checkout_dt = co.datetime
        if stats["last_visit"] is None or checkout_dt > stats["last_visit"]:
            stats["last_visit"] = checkout_dt

    result = []
    for entry in customer_stats.values():
        entry["total_spent"] = round(entry["total_spent"], 2)
        entry["total_hours"] = round(entry["total_minutes"] / 60, 2)
        entry["last_visit"] = (
            entry["last_visit"].isoformat() if entry["last_visit"] else None
        )
        del entry["total_minutes"]
        result.append(entry)

    result.sort(key=lambda x: x["total_spent"], reverse=True)

    return {
        "shop_id": str(shop_id),
        "since": since.isoformat(),
        "until": until.isoformat(),
        "total_customers": len(result),
        "top_customers": result[:limit],
    }
