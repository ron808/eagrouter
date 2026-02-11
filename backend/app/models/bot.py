# delivery bot — total bots = 5, every bot can have max 3 orders at once (from the assignment spec)

from sqlalchemy import Column, Integer, String, ForeignKey, Enum
from sqlalchemy.orm import relationship
import enum
from app.database import Base


class BotStatus(str, enum.Enum):
    IDLE = "IDLE"
    MOVING = "MOVING"
    PICKING_UP = "PICKING_UP"
    DELIVERING = "DELIVERING"


class Bot(Base):
    __tablename__ = "bots"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False)
    current_node_id = Column(Integer, ForeignKey("nodes.id"), nullable=True)
    status = Column(
        Enum(BotStatus),
        default=BotStatus.IDLE,
        nullable=False
    )
    max_capacity = Column(Integer, default=3, nullable=False)

    current_node = relationship("Node")
    # only active orders here (ASSIGNED/PICKED_UP), delivered ones don't count toward capacity
    orders = relationship(
        "Order",
        back_populates="bot",
        foreign_keys="Order.bot_id"
    )

    @property
    def current_order_count(self) -> int:
        if not self.orders:
            return 0
        return len([
            o for o in self.orders
            if o.status in ("ASSIGNED", "PICKED_UP")
        ])

    @property
    def available_capacity(self) -> int:
        return self.max_capacity - self.current_order_count

    @property
    def has_capacity(self) -> bool:
        return self.available_capacity > 0

    @property
    def is_available(self) -> bool:
        # a bot is available if it has capacity (< 3 active orders) and is idle or already moving
        return self.has_capacity and self.status in (BotStatus.IDLE, BotStatus.MOVING)

    def __repr__(self):
        return f"<Bot(id={self.id}, name={self.name}, status={self.status}, node={self.current_node_id})>"

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "status": self.status.value if self.status else None,
            "current_node_id": self.current_node_id,
            "location": {
                "x": self.current_node.x if self.current_node else None,
                "y": self.current_node.y if self.current_node else None,
            },
            "max_capacity": self.max_capacity,
            "current_order_count": self.current_order_count,
            "available_capacity": self.available_capacity,
        }
