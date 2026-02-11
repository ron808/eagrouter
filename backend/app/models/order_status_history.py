# order status history — audit trail for order state changes, populated by postgres triggers in alembic/versions/002_add_order_status_triggers.py

from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship
from app.database import Base


class OrderStatusHistory(Base):
    __tablename__ = "order_status_history"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(
        Integer,
        ForeignKey("orders.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    old_status = Column(String(20), nullable=True)
    new_status = Column(String(20), nullable=False)
    changed_at = Column(
        DateTime,
        default=func.now(),
        nullable=False,
        index=True
    )

    order = relationship("Order", back_populates="status_history")

    def __repr__(self):
        return f"<OrderStatusHistory(order={self.order_id}, {self.old_status} -> {self.new_status})>"

    def to_dict(self):
        return {
            "id": self.id,
            "order_id": self.order_id,
            "old_status": self.old_status,
            "new_status": self.new_status,
            "changed_at": self.changed_at.isoformat() if self.changed_at else None,
        }
