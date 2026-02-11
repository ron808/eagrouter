# order schemas - create, update, response, and status history

from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from app.schemas.enums import OrderStatusEnum


class OrderCreate(BaseModel):
    restaurant_id: int
    delivery_node_id: int


class OrderUpdate(BaseModel):
    delivery_node_id: Optional[int] = None
    status: Optional[OrderStatusEnum] = None


class OrderResponse(BaseModel):
    id: int
    restaurant_id: int
    restaurant_name: Optional[str] = None
    pickup_node_id: int
    pickup_address: str = ""
    delivery_node_id: int
    delivery_address: str = ""
    bot_id: Optional[int] = None
    bot_name: Optional[str] = None
    status: OrderStatusEnum
    created_at: Optional[datetime] = None
    assigned_at: Optional[datetime] = None
    picked_up_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class OrderStatusHistory(BaseModel):
    id: int
    order_id: int
    old_status: Optional[str]
    new_status: str
    changed_at: datetime

    class Config:
        from_attributes = True
