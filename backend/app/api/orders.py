import datetime
import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.deps import get_current_user, require_role
from app.database import get_db
from app.models.enums import OrderStatus, UserRole
from app.models.order import Order
from app.models.user import User
from app.schemas.order import OrderCreate, OrderOut, OrderStatusUpdate
from app.services.orders import (
    BookingNotFoundError,
    BookingOwnershipError,
    MenuItemNotFoundError,
    MenuItemUnavailableError,
    create_order as create_order_service,
    is_valid_status_transition,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/orders", tags=["orders"])


@router.post("", response_model=OrderOut, status_code=status.HTTP_201_CREATED)
async def create_order(
    payload: OrderCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Order:
    try:
        return await create_order_service(
            db, user_id=current_user.id, items=payload.items, booking_id=payload.booking_id
        )
    except MenuItemNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Menu item {exc.menu_item_id} not found"
        ) from exc
    except MenuItemUnavailableError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'"{exc.menu_item_name}" is not currently available',
        ) from exc
    except BookingNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found") from exc
    except BookingOwnershipError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="That booking does not belong to you"
        ) from exc


@router.get("/me", response_model=list[OrderOut])
async def list_my_orders(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[Order]:
    result = await db.execute(
        select(Order)
        .where(Order.user_id == current_user.id)
        .options(selectinload(Order.items))
        .order_by(Order.created_at.desc())
    )
    return list(result.scalars().unique().all())


@router.get(
    "",
    response_model=list[OrderOut],
    dependencies=[Depends(require_role(UserRole.staff_admin))],
)
async def list_orders(
    status_filter: OrderStatus | None = Query(default=None, alias="status"),
    date_from: datetime.date | None = Query(default=None),
    date_to: datetime.date | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
) -> list[Order]:
    query = select(Order).options(selectinload(Order.items)).order_by(Order.created_at.desc())

    if status_filter is not None:
        query = query.where(Order.status == status_filter)
    if date_from is not None:
        query = query.where(Order.created_at >= datetime.datetime.combine(date_from, datetime.time.min))
    if date_to is not None:
        query = query.where(
            Order.created_at < datetime.datetime.combine(date_to + datetime.timedelta(days=1), datetime.time.min)
        )

    result = await db.execute(query)
    return list(result.scalars().unique().all())


@router.patch(
    "/{order_id}",
    response_model=OrderOut,
    dependencies=[Depends(require_role(UserRole.staff_admin))],
)
async def update_order_status(
    order_id: uuid.UUID, payload: OrderStatusUpdate, db: AsyncSession = Depends(get_db)
) -> Order:
    result = await db.execute(
        select(Order).where(Order.id == order_id).options(selectinload(Order.items))
    )
    order = result.scalar_one_or_none()
    if order is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

    if not is_valid_status_transition(order.status, payload.status):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot change order status from {order.status.value} to {payload.status.value}",
        )

    order.status = payload.status
    # No refresh needed: status isn't server-generated, and expire_on_commit
    # is disabled, so the in-memory value (and the already-loaded `items`
    # relationship) survive the commit untouched.
    await db.commit()

    # Placeholder for the plan's "in-app notification on order status change":
    # real delivery (toast/badge/push to the customer) is a frontend concern
    # (Phase 6) since no client exists yet to receive it. This at least makes
    # every status change observable server-side in the meantime.
    logger.info("order %s status changed to %s", order.id, order.status.value)

    return order
