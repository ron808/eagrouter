# simulation schemas

from pydantic import BaseModel


class SimulationStatus(BaseModel):
    is_running: bool
    tick_count: int
    total_orders: int
    pending_orders: int
    delivered_orders: int
    active_bots: int
