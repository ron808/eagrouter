# node schemas - request/response models for grid nodes

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
