# grid node - a point on the 9x9 delivery map

from sqlalchemy import Column, Integer, Boolean, Index
from sqlalchemy.orm import relationship
from app.database import Base


class Node(Base):
    __tablename__ = "nodes"

    id = Column(Integer, primary_key=True, index=True)
    x = Column(Integer, nullable=False)
    y = Column(Integer, nullable=False)
    # true for the 14 houses where customers can get deliveries
    is_delivery_point = Column(Boolean, default=False, nullable=False)

    restaurant = relationship("Restaurant", back_populates="node", uselist=False)

    __table_args__ = (
        Index("idx_node_coordinates", "x", "y", unique=True),
    )

    def __repr__(self):
        return f"<Node(id={self.id}, x={self.x}, y={self.y}, delivery={self.is_delivery_point})>"

    def to_dict(self):
        return {
            "id": self.id,
            "x": self.x,
            "y": self.y,
            "is_delivery_point": self.is_delivery_point,
        }

    def distance_to(self, other: "Node") -> int:
        # manhattan distance, doesn't account for blocked paths
        return abs(self.x - other.x) + abs(self.y - other.y)
