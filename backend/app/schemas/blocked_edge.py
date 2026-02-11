# blocked edge schemas

from pydantic import BaseModel


class BlockedEdgeResponse(BaseModel):
    id: int
    from_node_id: int
    to_node_id: int

    class Config:
        from_attributes = True
