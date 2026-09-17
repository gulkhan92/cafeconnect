import uuid
from datetime import date as date_, time as time_

from sqlalchemy import Boolean, Date, ForeignKey, Integer, String, Time, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Table(Base):
    __tablename__ = "tables"
    __table_args__ = (UniqueConstraint("table_number", name="uq_tables_table_number"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    table_number: Mapped[str] = mapped_column(String(20), nullable=False)
    capacity: Mapped[int] = mapped_column(Integer, nullable=False)
    location_tag: Mapped[str | None] = mapped_column(String(50), nullable=True)

    slots: Mapped[list["TableSlot"]] = relationship(back_populates="table")


class TableSlot(Base):
    __tablename__ = "table_slots"
    __table_args__ = (
        UniqueConstraint("table_id", "date", "start_time", name="uq_table_slots_table_date_start"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    table_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tables.id", ondelete="CASCADE"), nullable=False
    )
    date: Mapped[date_] = mapped_column(Date, nullable=False)
    start_time: Mapped[time_] = mapped_column(Time, nullable=False)
    end_time: Mapped[time_] = mapped_column(Time, nullable=False)
    is_booked: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    booking_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("bookings.id", ondelete="SET NULL", use_alter=True, name="fk_table_slots_booking_id"),
        nullable=True,
    )

    table: Mapped["Table"] = relationship(back_populates="slots")
