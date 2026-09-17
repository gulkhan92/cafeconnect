import uuid
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.booking import Booking
from app.models.enums import OrderDataSource, OrderStatus
from app.models.menu import MenuItem
from app.models.order import Order, OrderItem
from app.schemas.order import OrderItemCreate

# No payment gateway is required for this phase: an order is created directly
# with status "placed" and paid at the counter / on pickup. Adding a real
# provider later (e.g. Stripe test mode) would only add a payment_status/
# payment_intent_id column and a webhook to confirm it — it would not change
# this schema or the flow below.


class OrderError(Exception):
    """Base class for order-creation failures the caller must translate into a response."""


class MenuItemNotFoundError(OrderError):
    def __init__(self, menu_item_id: uuid.UUID):
        self.menu_item_id = menu_item_id


class MenuItemUnavailableError(OrderError):
    def __init__(self, menu_item_name: str):
        self.menu_item_name = menu_item_name


class BookingNotFoundError(OrderError):
    pass


class BookingOwnershipError(OrderError):
    pass


_ALLOWED_STATUS_TRANSITIONS: dict[OrderStatus, set[OrderStatus]] = {
    OrderStatus.placed: {OrderStatus.preparing, OrderStatus.cancelled},
    OrderStatus.preparing: {OrderStatus.ready, OrderStatus.cancelled},
    OrderStatus.ready: {OrderStatus.completed},
    OrderStatus.completed: set(),
    OrderStatus.cancelled: set(),
}


class InvalidStatusTransitionError(OrderError):
    def __init__(self, current: OrderStatus, requested: OrderStatus):
        self.current = current
        self.requested = requested


def is_valid_status_transition(current: OrderStatus, requested: OrderStatus) -> bool:
    return requested in _ALLOWED_STATUS_TRANSITIONS[current]


async def create_order(
    db: AsyncSession,
    *,
    user_id: uuid.UUID,
    items: list[OrderItemCreate],
    booking_id: uuid.UUID | None,
) -> Order:
    if booking_id is not None:
        booking = await db.get(Booking, booking_id)
        if booking is None:
            raise BookingNotFoundError()
        if booking.user_id != user_id:
            raise BookingOwnershipError()

    menu_item_ids = [entry.menu_item_id for entry in items]
    result = await db.execute(select(MenuItem).where(MenuItem.id.in_(menu_item_ids)))
    menu_items_by_id = {item.id: item for item in result.scalars().all()}

    order_items: list[OrderItem] = []
    total_amount = Decimal("0")

    for entry in items:
        menu_item = menu_items_by_id.get(entry.menu_item_id)
        if menu_item is None:
            raise MenuItemNotFoundError(entry.menu_item_id)
        if not menu_item.is_available:
            raise MenuItemUnavailableError(menu_item.name)

        # Server-side price snapshot: the client's submitted price, if any, is
        # never trusted — only the menu's current price is used.
        unit_price = menu_item.price
        order_items.append(
            OrderItem(menu_item_id=menu_item.id, quantity=entry.quantity, unit_price_at_order_time=unit_price)
        )
        total_amount += unit_price * entry.quantity

    order = Order(
        user_id=user_id,
        booking_id=booking_id,
        status=OrderStatus.placed,
        total_amount=total_amount,
        source=OrderDataSource.live,
    )
    order.items = order_items

    db.add(order)
    await db.commit()
    # Only refresh the server-generated column we actually need. A bare
    # refresh() also expires the already-populated `items` relationship,
    # which would then try to lazy-load during response serialization —
    # outside any awaited context — and blow up with MissingGreenlet.
    await db.refresh(order, attribute_names=["created_at"])
    return order
