# Order management endpoints

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta

from app.database import get_db
from app.models import Order, Restaurant, Node, Bot
from app.models.order import OrderStatus
from app.models.bot import BotStatus
from app.schemas import OrderCreate, OrderUpdate, OrderResponse, OrderStatusHistory
from app.routers.grid import to_address

router = APIRouter()

# restaurant throttle: max 3 orders created within a 30-second window
RESTAURANT_MAX_ORDERS = 3
RESTAURANT_WINDOW_SECONDS = 30


def _order_response(o: Order) -> OrderResponse:
    # builds the response with the LR address format included for frontend display
    return OrderResponse(
        id=o.id,
        restaurant_id=o.restaurant_id,
        restaurant_name=o.restaurant.name if o.restaurant else None,
        pickup_node_id=o.pickup_node_id,
        pickup_address=to_address(o.pickup_node.x, o.pickup_node.y) if o.pickup_node else "",
        delivery_node_id=o.delivery_node_id,
        delivery_address=to_address(o.delivery_node.x, o.delivery_node.y) if o.delivery_node else "",
        bot_id=o.bot_id,
        bot_name=o.bot.name if o.bot else None,
        status=o.status,
        created_at=o.created_at,
        assigned_at=o.assigned_at,
        picked_up_at=o.picked_up_at,
        delivered_at=o.delivered_at,
    )


# READ -- list orders with optional status filter
@router.get("", response_model=List[OrderResponse])
def get_orders(
    status: Optional[str] = None,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    query = db.query(Order)

    if status:
        try:
            status_enum = OrderStatus(status.upper())
            query = query.filter(Order.status == status_enum)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid status: {status}")

    orders = query.order_by(Order.created_at.desc()).limit(limit).all()
    return [_order_response(o) for o in orders]


# CREATE -- place a new order at a restaurant
@router.post("", response_model=OrderResponse, status_code=201)
def create_order(order_data: OrderCreate, db: Session = Depends(get_db)):
    restaurant = db.query(Restaurant).filter(Restaurant.id == order_data.restaurant_id).first()
    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found")

    # restaurant rate limit: max 3 orders per 30s window — doesn't matter if orders got delivered or cancelled, the cooldown still applies
    window_start = datetime.utcnow() - timedelta(seconds=RESTAURANT_WINDOW_SECONDS)
    recent_count = db.query(Order).filter(
        Order.restaurant_id == restaurant.id,
        Order.created_at >= window_start,
    ).count()
    if recent_count >= RESTAURANT_MAX_ORDERS:
        raise HTTPException(
            status_code=429,
            detail=(
                f"Restaurant '{restaurant.name}' has received {recent_count} "
                f"orders in the last {RESTAURANT_WINDOW_SECONDS}s. "
                f"Max {RESTAURANT_MAX_ORDERS} allowed — please wait."
            ),
        )

    delivery_node = db.query(Node).filter(Node.id == order_data.delivery_node_id).first()
    if not delivery_node:
        raise HTTPException(status_code=404, detail="Delivery node not found")
    if not delivery_node.is_delivery_point:
        raise HTTPException(status_code=400, detail="Selected node is not a valid delivery point")

    order = Order(
        restaurant_id=restaurant.id,
        pickup_node_id=restaurant.node_id,
        delivery_node_id=delivery_node.id,
        status=OrderStatus.PENDING,
    )

    db.add(order)
    db.commit()
    db.refresh(order)

    # try to assign a bot right away so the user doesn't have to wait for the next tick
    try_assign_order(order, db)

    return _order_response(order)


# READ -- get a single order by id
@router.get("/{order_id}", response_model=OrderResponse)
def get_order(order_id: int, db: Session = Depends(get_db)):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return _order_response(order)


# UPDATE -- change delivery location (only while pending) or update status
@router.put("/{order_id}", response_model=OrderResponse)
def update_order(order_id: int, update_data: OrderUpdate, db: Session = Depends(get_db)):
    # only pending orders can change delivery location, and delivered/cancelled orders can't be touched at all
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if update_data.delivery_node_id is not None:
        if order.status != OrderStatus.PENDING:
            raise HTTPException(
                status_code=400,
                detail="Can only change delivery location for PENDING orders",
            )
        delivery_node = db.query(Node).filter(Node.id == update_data.delivery_node_id).first()
        if not delivery_node:
            raise HTTPException(status_code=404, detail="Delivery node not found")
        if not delivery_node.is_delivery_point:
            raise HTTPException(status_code=400, detail="Selected node is not a valid delivery point")
        order.delivery_node_id = delivery_node.id

    if update_data.status is not None:
        if order.status in (OrderStatus.DELIVERED, OrderStatus.CANCELLED):
            raise HTTPException(
                status_code=400,
                detail=f"Cannot update order with status {order.status.value}",
            )
        order.status = OrderStatus(update_data.status.value)

    db.commit()
    db.refresh(order)
    return _order_response(order)


# DELETE -- cancel an order (only if it hasn't been picked up yet)
@router.delete("/{order_id}", status_code=204)
def cancel_order(order_id: int, db: Session = Depends(get_db)):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if order.status not in [OrderStatus.PENDING, OrderStatus.ASSIGNED]:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot cancel order with status {order.status.value}",
        )

    # if this was the bot's only active order, free it up so it can take new ones
    if order.bot_id:
        other_orders = db.query(Order).filter(
            Order.bot_id == order.bot_id,
            Order.id != order.id,
            Order.status.in_([OrderStatus.ASSIGNED, OrderStatus.PICKED_UP]),
        ).count()

        if other_orders == 0:
            bot = db.query(Bot).filter(Bot.id == order.bot_id).first()
            if bot:
                bot.status = BotStatus.IDLE

    order.status = OrderStatus.CANCELLED
    db.commit()
    return None


@router.get("/{order_id}/history", response_model=List[OrderStatusHistory])
def get_order_history(order_id: int, db: Session = Depends(get_db)):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    from app.models import OrderStatusHistory as HistoryModel

    history = db.query(HistoryModel).filter(
        HistoryModel.order_id == order_id
    ).order_by(HistoryModel.changed_at.asc()).all()

    return [
        OrderStatusHistory(
            id=h.id,
            order_id=h.order_id,
            old_status=h.old_status,
            new_status=h.new_status,
            changed_at=h.changed_at,
        )
        for h in history
    ]


def try_assign_order(order: Order, db: Session) -> bool:
    # tries to immediately assign the order to the least-loaded idle/moving bot so it doesn't have to wait for the next simulation tick
    bots = db.query(Bot).filter(
        Bot.status.in_([BotStatus.IDLE, BotStatus.MOVING])
    ).all()

    best_bot = None
    best_load = float('inf')

    for bot in bots:
        current_orders = db.query(Order).filter(
            Order.bot_id == bot.id,
            Order.status.in_([OrderStatus.ASSIGNED, OrderStatus.PICKED_UP]),
        ).count()

        # strictly respect the bot's capacity limit
        if current_orders >= bot.max_capacity:
            continue

        # prefer the bot with the fewest active orders to spread the load evenly
        if current_orders < best_load:
            best_load = current_orders
            best_bot = bot

    if best_bot:
        order.bot_id = best_bot.id
        order.status = OrderStatus.ASSIGNED
        order.assigned_at = datetime.utcnow()

        if best_bot.status == BotStatus.IDLE:
            best_bot.status = BotStatus.MOVING

        db.commit()
        return True

    # no bot available right now -- stays PENDING until the simulation assigns it
    return False
