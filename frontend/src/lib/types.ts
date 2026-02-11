// I've defined these frontend interfaces to mirror our backend Pydantic models.
// Keeping these in sync is vital; if we modify the SQLAlchemy models or 
// FastAPI schemas, I need to make sure these types are updated here as well 
// to prevent any runtime mismatches in the React components.

// This represents a single location on our grid. 
// I'm using is_delivery_point to distinguish between regular nodes 
// and the houses where food actually gets delivered.
export interface Node {
  id: number;
  x: number;
  y: number;
  is_delivery_point: boolean;
  address: string;
}

// These are the restaurant locations. I've placed them on specific grid nodes 
// to act as the starting points for delivery pickups.
export interface Restaurant {
  id: number;
  name: string;
  node_id: number;
  x: number;
  y: number;
  address: string;
}

// I'm tracking blocked edges here to represent obstacles on the map.
// Bots use this information during pathfinding to avoid "forbidden" paths.
export interface BlockedEdge {
  id: number;
  from_node_id: number;
  to_node_id: number;
}

// This is the core Bot interface. I am tracking its real-time position,
// its current movement state, and the sequence of nodes it plans to visit.
export interface Bot {
  id: number;
  name: string;
  status: "IDLE" | "MOVING" | "PICKING_UP" | "DELIVERING";
  current_node_id: number;
  x: number;
  y: number;
  route: number[];
  target: {
    node_id: number;
    action: "PICKUP" | "DELIVER" | "STATION";
    order_id: number | null;
  } | null;
  active_orders: number;
}

// This represents a food delivery order. 
// It moves through several states: PENDING, ASSIGNED, PICKED_UP, and finally DELIVERED.
export interface Order {
  id: number;
  restaurant_id: number;
  restaurant_name: string;
  pickup_node_id: number;
  pickup_address: string;
  delivery_node_id: number;
  delivery_address: string;
  bot_id: number | null;
  bot_name: string | null;
  status: "PENDING" | "ASSIGNED" | "PICKED_UP" | "DELIVERED" | "CANCELLED";
}

// I've grouped the full grid layout here. This is what the GET /api/grid endpoint returns,
// and it's the foundation for our interactive map visualization.
export interface Grid {
  nodes: Node[];
  restaurants: Restaurant[];
  blocked_edges: BlockedEdge[];
  delivery_points: Node[];
}

// This provides a snapshot of the entire simulation. 
// I am using this to power the real-time stats row and the running/idle status indicator.
export interface SimulationStatus {
  is_running: boolean;
  tick_count: number;
  total_orders: number;
  pending_orders: number;
  delivered_orders: number;
  active_bots: number;
}
