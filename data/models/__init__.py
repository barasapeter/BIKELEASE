from __future__ import annotations

import enum
import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy import (
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class PaymentMethod(enum.StrEnum):
    CASH = "CASH"
    MPESA = "MPESA"


class MpesaTransactionStatus(enum.StrEnum):
    PENDING = "PENDING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class ShopOwner(Base):
    __tablename__ = "shop_owner"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    username: Mapped[str] = mapped_column(String(80), nullable=False, unique=True)
    pin_hash: Mapped[str] = mapped_column(String(255), nullable=False)

    datetime_registered: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    metadata_e: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    shops: Mapped[List["Shop"]] = relationship(
        back_populates="owner", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return (
            f"<ShopOwner(id={self.id}, "
            f"username='{self.username}', "
            f"name='{self.name}')>"
        )


class Shop(Base):
    __tablename__ = "shop"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    name: Mapped[str] = mapped_column(String(200), nullable=False)

    owner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("shop_owner.id", ondelete="RESTRICT"),
        nullable=False,
    )

    datetime_registered: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    metadata_e: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    owner: Mapped["ShopOwner"] = relationship(back_populates="shops")
    employees: Mapped[List["Employee"]] = relationship(
        back_populates="shop", cascade="all, delete-orphan"
    )
    bikes: Mapped[List["Bike"]] = relationship(
        back_populates="shop", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return (
            f"<Shop(id={self.id}, "
            f"name='{self.name}', "
            f"owner_id={self.owner_id})>"
        )


class Employee(Base):
    __tablename__ = "employee"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    shop_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("shop.id", ondelete="CASCADE"), nullable=False
    )

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    username: Mapped[str] = mapped_column(String(80), nullable=False, unique=True)
    pin_hash: Mapped[str] = mapped_column(String(255), nullable=False)

    datetime_registered: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    metadata_e: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    shop: Mapped["Shop"] = relationship(back_populates="employees")

    def __repr__(self) -> str:
        return (
            f"<Employee(id={self.id}, "
            f"username='{self.username}', "
            f"shop_id={self.shop_id})>"
        )


class Customer(Base):
    __tablename__ = "customer"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    primary_phone: Mapped[str] = mapped_column(String(32), nullable=False, unique=True)

    datetime_registered: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    metadata_e: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    sessions: Mapped[List["Session"]] = relationship(
        back_populates="customer", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return (
            f"<Customer(id={self.id}, "
            f"name='{self.name}', "
            f"primary_phone='{self.primary_phone}')>"
        )


class Bike(Base):
    __tablename__ = "bike"

    id: Mapped[str] = mapped_column(String(6), primary_key=True)  # e.g. "012345"
    nickname: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)

    rate_per_minute: Mapped[Numeric] = mapped_column(Numeric(10, 2), nullable=False)

    shop_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("shop.id", ondelete="CASCADE"), nullable=False
    )

    metadata_e: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    __table_args__ = (UniqueConstraint("shop_id", "id", name="uq_bike_shop_id_code"),)

    shop: Mapped["Shop"] = relationship(back_populates="bikes")
    sessions: Mapped[List["Session"]] = relationship(back_populates="bike")

    def __repr__(self) -> str:
        return (
            f"<Bike(id='{self.id}', "
            f"nickname='{self.nickname}', "
            f"shop_id={self.shop_id})>"
        )


class Session(Base):
    __tablename__ = "session"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    customer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("customer.id", ondelete="RESTRICT"),
        nullable=False,
    )
    bike_id: Mapped[str] = mapped_column(
        String(6), ForeignKey("bike.id", ondelete="RESTRICT"), nullable=False
    )

    rpm_on_allocate: Mapped[int] = mapped_column(Integer, nullable=False)

    start_datetime: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    stop_datetime: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    metadata_e: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    customer: Mapped["Customer"] = relationship(back_populates="sessions")
    bike: Mapped["Bike"] = relationship(back_populates="sessions")

    checkout: Mapped[Optional["SessionCheckout"]] = relationship(
        back_populates="session",
        uselist=False,
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return (
            f"<Session(id={self.id}, "
            f"customer_id={self.customer_id}, "
            f"bike_id='{self.bike_id}', "
            f"start={self.start_datetime}, "
            f"stop={self.stop_datetime})>"
        )


class SessionCheckout(Base):
    __tablename__ = "session_checkout"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("session.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )

    payment_method_enum: Mapped[PaymentMethod] = mapped_column(
        SAEnum(PaymentMethod, name="payment_method_enum"),
        nullable=False,
    )

    amount_paid: Mapped[Numeric] = mapped_column(Numeric(12, 2), nullable=False)
    duration_in_minutes: Mapped[int] = mapped_column(Integer, nullable=False)

    datetime: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    metadata_e: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    session: Mapped["Session"] = relationship(back_populates="checkout")

    mpesa: Mapped[Optional["MpesaCheckout"]] = relationship(
        back_populates="session_checkout",
        uselist=False,
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return (
            f"<SessionCheckout(id={self.id}, "
            f"session_id={self.session_id}, "
            f"payment_method={self.payment_method_enum}, "
            f"amount_paid={self.amount_paid})>"
        )


class MpesaCheckout(Base):
    __tablename__ = "mpesa_checkout"

    session_checkout_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("session_checkout.id", ondelete="CASCADE"),
        primary_key=True,
    )

    customer_MSISDN: Mapped[str] = mapped_column(String(32), nullable=False)
    mpesa_checkout_request_id: Mapped[str] = mapped_column(
        String(128), nullable=False, unique=True
    )

    transaction_status_desc: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True
    )
    transaction_status_enum: Mapped[MpesaTransactionStatus] = mapped_column(
        SAEnum(MpesaTransactionStatus, name="mpesa_transaction_status_enum"),
        nullable=False,
        default=MpesaTransactionStatus.PENDING,
    )

    session_checkout: Mapped["SessionCheckout"] = relationship(back_populates="mpesa")

    def __repr__(self) -> str:
        return (
            f"<MpesaCheckout(session_checkout_id={self.session_checkout_id}, "
            f"mpesa_checkout_request_id='{self.mpesa_checkout_request_id}', "
            f"status={self.transaction_status_enum})>"
        )
