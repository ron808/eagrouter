# schema for blocked edges -- these are grid connections bots can't travel through (think road closures)

from pydantic import BaseModel


class BlockedEdgeResponse(BaseModel):
    id: int
    from_node_id: int
    to_node_id: int

    class Config:
        from_attributes = True
