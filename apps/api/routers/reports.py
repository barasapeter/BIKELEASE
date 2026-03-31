from datetime import datetime, timedelta, date
from typing import Dict, Any, List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, case, extract, desc

from data.db import get_db
from data.models import (
    Shop,
    ShopOwner,
    Employee,
    Session as BikeSession,
    SessionCheckout,
    Bike,
    Customer,
    PaymentMethod,
)
from core.security import get_current_user

router = APIRouter()


# -------------------------------------------------------------------
# 🔐 AUTHORIZATION HELPER
# -------------------------------------------------------------------
def validate_shop_access(db: Session, shop_id, current_user):
    """
    Ensures that the requesting user has access to the shop.

    - ShopOwner: must own the shop
    - Employee: must belong to the shop
    """
    shop = db.get(Shop, shop_id)
    if not shop:
        raise HTTPException(status_code=404, detail="Shop not found")

    if isinstance(current_user, ShopOwner):
        if shop.owner_id != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")

    elif isinstance(current_user, Employee):
        if current_user.shop_id != shop_id:
            raise HTTPException(status_code=403, detail="Access denied")

    else:
        raise HTTPException(status_code=403, detail="Invalid user")

    return shop


# -------------------------------------------------------------------
# 1a. DAILY REVENUE REPORT
# -------------------------------------------------------------------
@router.get("/daily-revenue")
def daily_revenue_report(
    shop_id: str = Query(...),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Daily operational revenue report.

    Returns:
    - Total revenue today
    - Revenue by payment method
    - Number of rentals
    """

    validate_shop_access(db, shop_id, current_user)

    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)

    query = (
        db.query(
            func.coalesce(func.sum(SessionCheckout.amount_paid), 0).label("total"),
            func.count(SessionCheckout.id).label("rentals"),
        )
        .join(BikeSession)
        .join(Bike)
        .filter(
            Bike.shop_id == shop_id,
            SessionCheckout.datetime >= today_start,
        )
    ).first()

    payment_breakdown = (
        db.query(
            SessionCheckout.payment_method_enum,
            func.sum(SessionCheckout.amount_paid),
        )
        .join(BikeSession)
        .join(Bike)
        .filter(
            Bike.shop_id == shop_id,
            SessionCheckout.datetime >= today_start,
        )
        .group_by(SessionCheckout.payment_method_enum)
        .all()
    )

    return {
        "total_revenue": float(query.total),
        "total_rentals": query.rentals,
        "payment_breakdown": {p[0].value: float(p[1]) for p in payment_breakdown},
    }


# -------------------------------------------------------------------
# 1b. WEEKLY FINANCIAL REPORT
# -------------------------------------------------------------------
@router.get("/weekly-financials")
def weekly_financials(
    shop_id: str = Query(...),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Weekly financial summary.

    Returns:
    - Total revenue
    - Revenue per bike
    - Most profitable bikes
    """

    validate_shop_access(db, shop_id, current_user)

    start = datetime.utcnow() - timedelta(days=7)

    revenue_per_bike = (
        db.query(
            Bike.id,
            func.sum(SessionCheckout.amount_paid).label("revenue"),
        )
        .join(BikeSession)
        .join(SessionCheckout)
        .filter(
            Bike.shop_id == shop_id,
            SessionCheckout.datetime >= start,
        )
        .group_by(Bike.id)
        .all()
    )

    total = sum(r.revenue or 0 for r in revenue_per_bike)

    most_profitable = sorted(
        revenue_per_bike, key=lambda x: x.revenue or 0, reverse=True
    )[:5]

    return {
        "total_revenue": float(total),
        "revenue_per_bike": {r.id: float(r.revenue or 0) for r in revenue_per_bike},
        "top_5_bikes": [
            {"bike_id": r.id, "revenue": float(r.revenue or 0)} for r in most_profitable
        ],
    }


# -------------------------------------------------------------------
# 1c. BIKE UTILIZATION REPORT
# -------------------------------------------------------------------
@router.get("/bike-utilization")
def bike_utilization(
    shop_id: str = Query(...),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Bike usage statistics.

    Returns per bike:
    - rental count
    - total hours used
    - revenue generated
    """

    validate_shop_access(db, shop_id, current_user)

    results = (
        db.query(
            Bike.id,
            func.count(BikeSession.id).label("rentals"),
            func.coalesce(func.sum(SessionCheckout.duration_in_minutes), 0).label(
                "minutes"
            ),
            func.coalesce(func.sum(SessionCheckout.amount_paid), 0).label("revenue"),
        )
        .outerjoin(BikeSession)
        .outerjoin(SessionCheckout)
        .filter(Bike.shop_id == shop_id)
        .group_by(Bike.id)
        .all()
    )

    return [
        {
            "bike_id": r.id,
            "total_rentals": r.rentals,
            "total_hours": float(r.minutes or 0) / 60,
            "revenue": float(r.revenue or 0),
        }
        for r in results
    ]


# -------------------------------------------------------------------
# 1d. IDLE BIKE REPORT
# -------------------------------------------------------------------
@router.get("/idle-bikes")
def idle_bikes(
    shop_id: str = Query(...),
    idle_minutes: int = Query(60),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Returns bikes that have not been used in the last X minutes.
    """

    validate_shop_access(db, shop_id, current_user)

    threshold = datetime.utcnow() - timedelta(minutes=idle_minutes)

    subquery = (
        db.query(
            BikeSession.bike_id,
            func.max(BikeSession.start_datetime).label("last_used"),
        )
        .group_by(BikeSession.bike_id)
        .subquery()
    )

    bikes = (
        db.query(Bike.id, subquery.c.last_used)
        .outerjoin(subquery, Bike.id == subquery.c.bike_id)
        .filter(
            Bike.shop_id == shop_id,
            case(
                (subquery.c.last_used == None, True),
                else_=subquery.c.last_used < threshold,
            ),
        )
        .all()
    )

    return [
        {
            "bike_id": b.id,
            "last_used": b.last_used,
        }
        for b in bikes
    ]


# -------------------------------------------------------------------
# 1e. CUSTOMER REPORT
# -------------------------------------------------------------------
@router.get("/customer-insights")
def customer_insights(
    shop_id: str = Query(...),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Customer analytics.

    Returns:
    - Most frequent renters
    - Total spent
    - Total hours rented
    """

    validate_shop_access(db, shop_id, current_user)

    results = (
        db.query(
            Customer.id,
            Customer.name,
            func.count(BikeSession.id).label("rentals"),
            func.coalesce(func.sum(SessionCheckout.amount_paid), 0).label("spent"),
            func.coalesce(func.sum(SessionCheckout.duration_in_minutes), 0).label(
                "minutes"
            ),
        )
        .join(BikeSession)
        .join(Bike)
        .outerjoin(SessionCheckout)
        .filter(Bike.shop_id == shop_id)
        .group_by(Customer.id)
        .order_by(desc("rentals"))
        .limit(10)
        .all()
    )

    return [
        {
            "customer_id": r.id,
            "name": r.name,
            "total_rentals": r.rentals,
            "total_spent": float(r.spent or 0),
            "total_hours": float(r.minutes or 0) / 60,
        }
        for r in results
    ]
