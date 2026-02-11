from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models import Bot, Order
from app.models.order import OrderStatus
from app.schemas import BotResponse, OrderResponse

router = APIRouter()


@router.get("", response_model=List[BotResponse])
def get_bots(db: Session = Depends(get_db)):
    bots = db.query(Bot).all()

    responses = []
    for bot in bots:
        active_orders = db.query(Order).filter(
            Order.bot_id == bot.id,
            Order.status.in_([OrderStatus.ASSIGNED, OrderStatus.PICKED_UP])
        ).count()

        responses.append(BotResponse(
            id=bot.id,
            name=bot.name,
            status=bot.status,
            current_node_id=bot.current_node_id,
            x=bot.current_node.x if bot.current_node else None,
            y=bot.current_node.y if bot.current_node else None,
            max_capacity=bot.max_capacity,
            current_order_count=active_orders,
            available_capacity=bot.max_capacity - active_orders
        ))

    return responses


@router.get("/{bot_id}", response_model=BotResponse)
def get_bot(bot_id: int, db: Session = Depends(get_db)):
    bot = db.query(Bot).filter(Bot.id == bot_id).first()
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")

    active_orders = db.query(Order).filter(
        Order.bot_id == bot.id,
        Order.status.in_([OrderStatus.ASSIGNED, OrderStatus.PICKED_UP])
    ).count()

    return BotResponse(
        id=bot.id,
        name=bot.name,
        status=bot.status,
        current_node_id=bot.current_node_id,
        x=bot.current_node.x if bot.current_node else None,
        y=bot.current_node.y if bot.current_node else None,
        max_capacity=bot.max_capacity,
        current_order_count=active_orders,
        available_capacity=bot.max_capacity - active_orders
    )


@router.get("/{bot_id}/orders", response_model=List[OrderResponse])
def get_bot_orders(bot_id: int, db: Session = Depends(get_db)):
    bot = db.query(Bot).filter(Bot.id == bot_id).first()
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")

    orders = db.query(Order).filter(
        Order.bot_id == bot_id,
        Order.status.in_([OrderStatus.ASSIGNED, OrderStatus.PICKED_UP])
    ).all()

    return [
        OrderResponse(
            id=o.id,
            restaurant_id=o.restaurant_id,
            restaurant_name=o.restaurant.name if o.restaurant else None,
            pickup_node_id=o.pickup_node_id,
            delivery_node_id=o.delivery_node_id,
            bot_id=o.bot_id,
            bot_name=o.bot.name if o.bot else None,
            status=o.status,
            created_at=o.created_at,
            assigned_at=o.assigned_at,
            picked_up_at=o.picked_up_at,
            delivered_at=o.delivered_at
        )
        for o in orders
    ]
