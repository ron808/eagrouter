# shared enums used across the pydantic schemas
# these mirror the sqlalchemy enums but live on the API side

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
