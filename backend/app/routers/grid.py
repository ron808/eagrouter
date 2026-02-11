from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models import Node, Restaurant, BlockedEdge
from app.schemas import (
    NodeResponse,
    RestaurantResponse,
    BlockedEdgeResponse,
    GridResponse
)

router = APIRouter()


def to_address(x: int, y: int) -> str:
    # per the spec: "Address = L(i=0~N, j=0~N) => Ex: Pizza=LR74"
    # so we turn grid coords into a human-friendly address like LR74
    return f"LR{x}{y}"


def node_to_response(node: Node) -> NodeResponse:
    return NodeResponse(
        id=node.id,
        x=node.x,
        y=node.y,
        is_delivery_point=node.is_delivery_point,
        address=to_address(node.x, node.y),
    )


@router.get("", response_model=GridResponse)
def get_grid(db: Session = Depends(get_db)):
    # returns everything the frontend needs to draw the map in one shot
    nodes = db.query(Node).all()

    restaurants = db.query(Restaurant).all()
    restaurant_responses = []
    for r in restaurants:
        x = r.node.x if r.node else 0
        y = r.node.y if r.node else 0
        restaurant_responses.append(RestaurantResponse(
            id=r.id,
            name=r.name,
            node_id=r.node_id,
            x=x,
            y=y,
            address=to_address(x, y),
        ))

    blocked_edges = db.query(BlockedEdge).all()
    delivery_points = db.query(Node).filter(Node.is_delivery_point == True).all()

    return GridResponse(
        nodes=[node_to_response(n) for n in nodes],
        restaurants=restaurant_responses,
        blocked_edges=[BlockedEdgeResponse.model_validate(e) for e in blocked_edges],
        delivery_points=[node_to_response(d) for d in delivery_points],
    )


@router.get("/nodes", response_model=List[NodeResponse])
def get_nodes(db: Session = Depends(get_db)):
    nodes = db.query(Node).all()
    return [node_to_response(n) for n in nodes]


@router.get("/nodes/{node_id}", response_model=NodeResponse)
def get_node(node_id: int, db: Session = Depends(get_db)):
    node = db.query(Node).filter(Node.id == node_id).first()
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    return node_to_response(node)


@router.get("/restaurants", response_model=List[RestaurantResponse])
def get_restaurants(db: Session = Depends(get_db)):
    restaurants = db.query(Restaurant).all()
    return [
        RestaurantResponse(
            id=r.id,
            name=r.name,
            node_id=r.node_id,
            x=r.node.x if r.node else None,
            y=r.node.y if r.node else None,
            address=to_address(r.node.x, r.node.y) if r.node else "",
        )
        for r in restaurants
    ]


@router.get("/delivery-points", response_model=List[NodeResponse])
def get_delivery_points(db: Session = Depends(get_db)):
    delivery_points = db.query(Node).filter(Node.is_delivery_point == True).all()
    return [node_to_response(d) for d in delivery_points]


@router.get("/blocked-edges", response_model=List[BlockedEdgeResponse])
def get_blocked_edges(db: Session = Depends(get_db)):
    edges = db.query(BlockedEdge).all()
    return [BlockedEdgeResponse.model_validate(e) for e in edges]
