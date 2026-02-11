# restaurant schemas

from pydantic import BaseModel
from typing import Optional


class RestaurantResponse(BaseModel):
    id: int
    name: str
    node_id: int
    x: Optional[int] = None
    y: Optional[int] = None
    address: str = ""

    class Config:
        from_attributes = True
