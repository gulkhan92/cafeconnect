import datetime
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, require_role
from app.database import get_db
from app.models.booking import Booking
from app.models.enums import BookingStatus, UserRole
from app.models.table import TableSlot
from app.models.user import User
from app.schemas.booking import BookingCreate, BookingOut, BookingStatusUpdate
from app.services.bookings import (
    CapacityExceededError,
    SlotAlreadyBookedError,
    SlotNotFoundError,
    create_booking as create_booking_service,
)

router = APIRouter(prefix="/bookings", tags=["bookings"])


@router.post("", response_model=BookingOut, status_code=status.HTTP_201_CREATED)
async def create_booking(
    payload: BookingCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Booking:
    try:
        return await create_booking_service(
            db,
            user_id=current_user.id,
            slot_id=payload.slot_id,
            party_size=payload.party_size,
            created_via=payload.created_via,
        )
    except SlotNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Table slot not found") from exc
    except SlotAlreadyBookedError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="This slot is already booked"
        ) from exc
    except CapacityExceededError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Party size exceeds the capacity of this table",
        ) from exc


@router.get("/me", response_model=list[BookingOut])
async def list_my_bookings(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[Booking]:
    result = await db.execute(
        select(Booking)
        .where(Booking.user_id == current_user.id)
        .order_by(Booking.created_at.desc())
    )
    return list(result.scalars().all())


@router.get(
    "",
    response_model=list[BookingOut],
    dependencies=[Depends(require_role(UserRole.staff_admin))],
)
async def list_bookings(
    booking_date: datetime.date | None = Query(default=None, alias="date"),
    status_filter: BookingStatus | None = Query(default=None, alias="status"),
    db: AsyncSession = Depends(get_db),
) -> list[Booking]:
    query = select(Booking).order_by(Booking.created_at.desc())

    if booking_date is not None:
        query = query.join(TableSlot, Booking.slot_id == TableSlot.id).where(
            TableSlot.date == booking_date
        )

    if status_filter is not None:
        query = query.where(Booking.status == status_filter)

    result = await db.execute(query)
    return list(result.scalars().all())


@router.patch(
    "/{booking_id}",
    response_model=BookingOut,
    dependencies=[Depends(require_role(UserRole.staff_admin))],
)
async def update_booking_status(
    booking_id: uuid.UUID, payload: BookingStatusUpdate, db: AsyncSession = Depends(get_db)
) -> Booking:
    booking = await db.get(Booking, booking_id)
    if booking is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")

    booking.status = payload.status

    if payload.status == BookingStatus.cancelled:
        slot = await db.get(TableSlot, booking.slot_id)
        if slot is not None:
            slot.is_booked = False
            slot.booking_id = None

    await db.commit()
    await db.refresh(booking)
    return booking
