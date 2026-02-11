# restaurant — pickup locations where bots collect food

from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class Restaurant(Base):
    __tablename__ = "restaurants"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False, index=True)
    node_id = Column(Integer, ForeignKey("nodes.id"), nullable=False, unique=True)

    node = relationship("Node", back_populates="restaurant")
    orders = relationship("Order", back_populates="restaurant")

    def __repr__(self):
        return f"<Restaurant(id={self.id}, name={self.name}, node_id={self.node_id})>"

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "node_id": self.node_id,
            "location": {
                "x": self.node.x if self.node else None,
                "y": self.node.y if self.node else None,
            }
        }
