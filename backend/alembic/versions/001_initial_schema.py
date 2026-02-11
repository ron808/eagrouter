"""Initial schema - create all tables

Revision ID: 001
Revises: None
Create Date: 2025-01-01 00:00:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # grid nodes -- every intersection on the town map, loaded from sample_data.csv
    op.create_table(
        "nodes",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("x", sa.Integer(), nullable=False),
        sa.Column("y", sa.Integer(), nullable=False),
        sa.Column("is_delivery_point", sa.Boolean(), nullable=False, server_default="false"),
    )
    op.create_index("idx_node_coordinates", "nodes", ["x", "y"], unique=True)

    # restaurants -- the 4 pickup locations (RAMEN, CURRY, PIZZA, SUSHI) where bots collect food
    op.create_table(
        "restaurants",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(50), unique=True, nullable=False),
        sa.Column("node_id", sa.Integer(), sa.ForeignKey("nodes.id"), nullable=False, unique=True),
    )

    # delivery bots -- autonomous robots that carry orders around the grid
    op.create_table(
        "bots",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(50), unique=True, nullable=False),
        sa.Column("current_node_id", sa.Integer(), sa.ForeignKey("nodes.id"), nullable=True),
        sa.Column("status", sa.Enum("IDLE", "MOVING", "PICKING_UP", "DELIVERING", name="botstatus"), nullable=False, server_default="IDLE"),
        sa.Column("max_capacity", sa.Integer(), nullable=False, server_default="3"),
    )

    # orders -- tracks each delivery from creation to completion
    op.create_table(
        "orders",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("restaurant_id", sa.Integer(), sa.ForeignKey("restaurants.id"), nullable=False),
        sa.Column("pickup_node_id", sa.Integer(), sa.ForeignKey("nodes.id"), nullable=False),
        sa.Column("delivery_node_id", sa.Integer(), sa.ForeignKey("nodes.id"), nullable=False),
        sa.Column("bot_id", sa.Integer(), sa.ForeignKey("bots.id"), nullable=True),
        sa.Column("status", sa.Enum("PENDING", "ASSIGNED", "PICKED_UP", "DELIVERED", "CANCELLED", name="orderstatus"), nullable=False, server_default="PENDING"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("assigned_at", sa.DateTime(), nullable=True),
        sa.Column("picked_up_at", sa.DateTime(), nullable=True),
        sa.Column("delivered_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_orders_status", "orders", ["status"])
    op.create_index("ix_orders_bot_id", "orders", ["bot_id"])

    # blocked edges -- impassable paths from BlockedPaths.csv that force bots to find alternate routes
    op.create_table(
        "blocked_edges",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("from_node_id", sa.Integer(), sa.ForeignKey("nodes.id"), nullable=False),
        sa.Column("to_node_id", sa.Integer(), sa.ForeignKey("nodes.id"), nullable=False),
        sa.UniqueConstraint("from_node_id", "to_node_id", name="unique_blocked_edge"),
    )
    op.create_index("idx_blocked_edge_lookup", "blocked_edges", ["from_node_id", "to_node_id"])

    # audit trail for order status changes -- auto-populated by postgres triggers (advanced DB concept)
    op.create_table(
        "order_status_history",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("order_id", sa.Integer(), sa.ForeignKey("orders.id", ondelete="CASCADE"), nullable=False),
        sa.Column("old_status", sa.String(20), nullable=True),
        sa.Column("new_status", sa.String(20), nullable=False),
        sa.Column("changed_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_order_status_history_order_id", "order_status_history", ["order_id"])


def downgrade() -> None:
    op.drop_table("order_status_history")
    op.drop_table("blocked_edges")
    op.drop_table("orders")
    op.drop_table("bots")
    op.drop_table("restaurants")
    op.drop_table("nodes")
    op.execute("DROP TYPE IF EXISTS botstatus")
    op.execute("DROP TYPE IF EXISTS orderstatus")
