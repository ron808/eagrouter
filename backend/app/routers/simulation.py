# simulation control endpoints -- start, stop, reset, and tick the delivery simulation
# per the spec: "View real-time updates on delivery status"
# the frontend polls /tick and /bots/positions to show live bot movement on the grid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import Dict, List

from app.database import get_db
from app.models import Order, Bot
from app.models.order import OrderStatus
from app.models.bot import BotStatus
from app.schemas import SimulationStatus, BotResponse
from app.services.simulation import SimulationService

router = APIRouter()

simulation_state = {
    "is_running": False,
    "tick_count": 0
}

_simulation_service = None


def get_simulation_service(db: Session) -> SimulationService:
    return SimulationService(db)


@router.get("/status", response_model=SimulationStatus)
def get_simulation_status(db: Session = Depends(get_db)):
    # gives the frontend a snapshot of the whole simulation state
    total_orders = db.query(Order).count()
    pending_orders = db.query(Order).filter(Order.status == OrderStatus.PENDING).count()
    delivered_orders = db.query(Order).filter(Order.status == OrderStatus.DELIVERED).count()
    active_bots = db.query(Bot).filter(Bot.status != BotStatus.IDLE).count()

    return SimulationStatus(
        is_running=simulation_state["is_running"],
        tick_count=simulation_state["tick_count"],
        total_orders=total_orders,
        pending_orders=pending_orders,
        delivered_orders=delivered_orders,
        active_bots=active_bots
    )


@router.post("/start")
def start_simulation():
    simulation_state["is_running"] = True
    return {"message": "Simulation started", "is_running": True}


@router.post("/stop")
def stop_simulation():
    simulation_state["is_running"] = False
    return {"message": "Simulation stopped", "is_running": False}


@router.post("/reset")
def reset_simulation(db: Session = Depends(get_db)):
    # wipes the slate clean -- cancels in-flight orders, resets bots to idle at start position
    simulation_state["is_running"] = False
    simulation_state["tick_count"] = 0

    # clear the restaurant cooldown tracking and tick counter too
    SimulationService._tick_counter = 0
    SimulationService._restaurant_order_log = {}

    db.query(Order).filter(
        Order.status.in_([OrderStatus.PENDING, OrderStatus.ASSIGNED, OrderStatus.PICKED_UP])
    ).update({Order.status: OrderStatus.CANCELLED}, synchronize_session=False)

    from app.models import Node
    start_node = db.query(Node).first()
    start_node_id = start_node.id if start_node else None

    db.query(Bot).update({
        Bot.status: BotStatus.IDLE,
        Bot.current_node_id: start_node_id
    }, synchronize_session=False)

    db.commit()

    return {"message": "Simulation reset", "is_running": False, "tick_count": 0}


@router.post("/tick")
def simulation_tick(db: Session = Depends(get_db)):
    # one tick = assign orders -> calculate routes -> move bots -> handle pickups/deliveries
    if not simulation_state["is_running"]:
        return {
            "message": "Simulation is not running",
            "tick": simulation_state["tick_count"],
            "results": None
        }

    service = get_simulation_service(db)
    results = service.tick()

    simulation_state["tick_count"] += 1

    return {
        "message": "Tick processed",
        "tick": simulation_state["tick_count"],
        "results": results
    }


@router.get("/bots/positions")
def get_bot_positions(db: Session = Depends(get_db)):
    # real-time bot positions, routes, and targets for the frontend map display
    service = get_simulation_service(db)
    bots = db.query(Bot).all()

    positions = []
    for bot in bots:
        route = service.get_bot_route(bot.id)
        target = service.get_bot_target(bot.id)

        active_orders = db.query(Order).filter(
            Order.bot_id == bot.id,
            Order.status.in_([OrderStatus.ASSIGNED, OrderStatus.PICKED_UP])
        ).count()

        positions.append({
            "id": bot.id,
            "name": bot.name,
            "status": bot.status.value,
            "current_node_id": bot.current_node_id,
            "x": bot.current_node.x if bot.current_node else None,
            "y": bot.current_node.y if bot.current_node else None,
            "route": route,
            "target": {
                "node_id": target[0] if target else None,
                "action": target[1] if target else None,
                "order_id": target[2] if target else None
            } if target else None,
            "active_orders": active_orders
        })

    return {"bots": positions, "tick": simulation_state["tick_count"]}
