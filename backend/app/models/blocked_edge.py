# blocked edge — impassable path between two adjacent nodes, loaded from BlockedPaths.csv per the assignment

from sqlalchemy import Column, Integer, ForeignKey, Index, UniqueConstraint
from sqlalchemy.orm import relationship
from app.database import Base


class BlockedEdge(Base):
    __tablename__ = "blocked_edges"

    id = Column(Integer, primary_key=True, index=True)
    from_node_id = Column(
        Integer,
        ForeignKey("nodes.id"),
        nullable=False,
        index=True
    )
    to_node_id = Column(
        Integer,
        ForeignKey("nodes.id"),
        nullable=False,
        index=True
    )

    from_node = relationship("Node", foreign_keys=[from_node_id])
    to_node = relationship("Node", foreign_keys=[to_node_id])

    # we store each blocked edge once (from < to), pathfinding checks both directions
    __table_args__ = (
        UniqueConstraint('from_node_id', 'to_node_id', name='unique_blocked_edge'),
        Index('idx_blocked_edge_lookup', 'from_node_id', 'to_node_id'),
    )

    def __repr__(self):
        return f"<BlockedEdge(from={self.from_node_id}, to={self.to_node_id})>"

    def to_dict(self):
        return {
            "id": self.id,
            "from_node_id": self.from_node_id,
            "to_node_id": self.to_node_id,
            "from_location": {
                "x": self.from_node.x if self.from_node else None,
                "y": self.from_node.y if self.from_node else None,
            },
            "to_location": {
                "x": self.to_node.x if self.to_node else None,
                "y": self.to_node.y if self.to_node else None,
            },
        }

    @staticmethod
    def is_blocked(from_id: int, to_id: int, blocked_set: set) -> bool:
        # checks both directions — if A->B is blocked, B->A is blocked too
        return (from_id, to_id) in blocked_set or (to_id, from_id) in blocked_set
