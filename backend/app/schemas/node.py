# schemas for grid nodes -- address is a human-readable label like "A1" derived from (x, y) coords

from pydantic import BaseModel


class NodeBase(BaseModel):
    x: int
    y: int
    is_delivery_point: bool = False


class NodeResponse(NodeBase):
    id: int
    address: str = ""

    class Config:
        from_attributes = True
