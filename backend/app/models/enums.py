import enum


class UserRole(str, enum.Enum):
    customer = "customer"
    staff_admin = "staff_admin"


class BookingStatus(str, enum.Enum):
    pending = "pending"
    confirmed = "confirmed"
    cancelled = "cancelled"


class BookingSource(str, enum.Enum):
    chatbot = "chatbot"
    manual = "manual"


class OrderStatus(str, enum.Enum):
    placed = "placed"
    preparing = "preparing"
    ready = "ready"
    completed = "completed"
    cancelled = "cancelled"


class OrderDataSource(str, enum.Enum):
    seed_demo = "seed_demo"
    live = "live"


class ChatRole(str, enum.Enum):
    user = "user"
    assistant = "assistant"
