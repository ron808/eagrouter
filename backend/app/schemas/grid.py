# the combined payload the frontend uses to draw the entire interactive map (nodes, restaurants, edges, delivery points)

from pydantic import BaseModel
from typing import List
from app.schemas.node import NodeResponse
from app.schemas.restaurant import RestaurantResponse
from app.schemas.blocked_edge import BlockedEdgeResponse


class GridResponse(BaseModel):
    nodes: List[NodeResponse]
    restaurants: List[RestaurantResponse]
    blocked_edges: List[BlockedEdgeResponse]
    delivery_points: List[NodeResponse]
