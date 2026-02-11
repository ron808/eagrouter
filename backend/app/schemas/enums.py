# API-side enums that mirror our SQLAlchemy enums -- shared across all pydantic schemas

from enum import Enum


class OrderStatusEnum(str, Enum):
    PENDING = "PENDING"
    ASSIGNED = "ASSIGNED"
    PICKED_UP = "PICKED_UP"
    DELIVERED = "DELIVERED"
    CANCELLED = "CANCELLED"


class BotStatusEnum(str, Enum):
    IDLE = "IDLE"
    MOVING = "MOVING"
    PICKING_UP = "PICKING_UP"
    DELIVERING = "DELIVERING"
