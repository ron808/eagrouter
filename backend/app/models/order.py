# order — a food delivery request, lifecycle: PENDING -> ASSIGNED -> PICKED_UP -> DELIVERED (or CANCELLED)

from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Enum, func
from sqlalchemy.orm import relationship
import enum
from datetime import datetime
from app.database import Base


class OrderStatus(str, enum.Enum):
    PENDING = "PENDING"
    ASSIGNED = "ASSIGNED"
    PICKED_UP = "PICKED_UP"
    DELIVERED = "DELIVERED"
    CANCELLED = "CANCELLED"


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    restaurant_id = Column(
        Integer,
        ForeignKey("restaurants.id"),
        nullable=False,
        index=True
    )
    # denormalized from restaurant.node_id for easier queries - this took me a while to figure out
    pickup_node_id = Column(
        Integer,
        ForeignKey("nodes.id"),
        nullable=False
    )
    delivery_node_id = Column(
        Integer,
        ForeignKey("nodes.id"),
        nullable=False,
        index=True
    )
    bot_id = Column(
        Integer,
        ForeignKey("bots.id"),
        nullable=True,
        index=True
    )
    status = Column(
        Enum(OrderStatus),
        default=OrderStatus.PENDING,
        nullable=False,
        index=True
    )

    # timestamps for tracking each stage of the order lifecycle
    created_at = Column(
        DateTime,
        default=func.now(),
        nullable=False
    )
    assigned_at = Column(DateTime, nullable=True)
    picked_up_at = Column(DateTime, nullable=True)
    delivered_at = Column(DateTime, nullable=True)

    restaurant = relationship("Restaurant", back_populates="orders")
    pickup_node = relationship("Node", foreign_keys=[pickup_node_id])
    delivery_node = relationship("Node", foreign_keys=[delivery_node_id])
    bot = relationship("Bot", back_populates="orders")
    status_history = relationship(
        "OrderStatusHistory",
        back_populates="order",
        order_by="OrderStatusHistory.changed_at"
    )

    def __repr__(self):
        return f"<Order(id={self.id}, restaurant={self.restaurant_id}, status={self.status}, bot={self.bot_id})>"

    def to_dict(self):
        return {
            "id": self.id,
            "restaurant_id": self.restaurant_id,
            "restaurant_name": self.restaurant.name if self.restaurant else None,
            "pickup_node_id": self.pickup_node_id,
            "pickup_location": {
                "x": self.pickup_node.x if self.pickup_node else None,
                "y": self.pickup_node.y if self.pickup_node else None,
            },
            "delivery_node_id": self.delivery_node_id,
            "delivery_location": {
                "x": self.delivery_node.x if self.delivery_node else None,
                "y": self.delivery_node.y if self.delivery_node else None,
            },
            "bot_id": self.bot_id,
            "bot_name": self.bot.name if self.bot else None,
            "status": self.status.value if self.status else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "assigned_at": self.assigned_at.isoformat() if self.assigned_at else None,
            "picked_up_at": self.picked_up_at.isoformat() if self.picked_up_at else None,
            "delivered_at": self.delivered_at.isoformat() if self.delivered_at else None,
        }

    def assign_to_bot(self, bot_id: int) -> None:
        self.bot_id = bot_id
        self.status = OrderStatus.ASSIGNED
        self.assigned_at = datetime.utcnow()

    def mark_picked_up(self) -> None:
        self.status = OrderStatus.PICKED_UP
        self.picked_up_at = datetime.utcnow()

    def mark_delivered(self) -> None:
        self.status = OrderStatus.DELIVERED
        self.delivered_at = datetime.utcnow()

    def cancel(self) -> None:
        self.status = OrderStatus.CANCELLED
