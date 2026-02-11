# response schema for delivery bots -- includes position, capacity, and current workload

from pydantic import BaseModel
from typing import Optional
from app.schemas.enums import BotStatusEnum


class BotResponse(BaseModel):
    id: int
    name: str
    status: BotStatusEnum
    current_node_id: Optional[int]
    x: Optional[int] = None
    y: Optional[int] = None
    max_capacity: int
    current_order_count: int = 0
    available_capacity: int = 3

    class Config:
        from_attributes = True
