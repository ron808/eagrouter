// Frontend type definitions — these mirror the backend Pydantic schemas exactly.
// If you change a model on the FastAPI side, update it here too or things will break.

// a single point on the grid map; delivery houses have is_delivery_point = true
export interface Node {
    id: number;
    x: number;
    y: number;
    is_delivery_point: boolean;
    address: string;
  }

  // restaurant sitting on a specific node — the place where bots pick up food
  export interface Restaurant {
    id: number;
    name: string;
    node_id: number;
    x: number;
    y: number;
    address: string;
  }

  // an edge between two nodes that bots can't travel through (obstacle)
  export interface BlockedEdge {
    id: number;
    from_node_id: number;
    to_node_id: number;
  }

  // delivery bot — tracks position, status, current route, and what it's working on
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
      action: "pickup" | "deliver";
      order_id: number;
    } | null;
    active_orders: number;
  }

  // a food delivery order — goes through PENDING -> ASSIGNED -> PICKED_UP -> DELIVERED
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

  // the full grid layout returned by GET /api/grid — used for the interactive map visualization
  export interface Grid {
    nodes: Node[];
    restaurants: Restaurant[];
    blocked_edges: BlockedEdge[];
    delivery_points: Node[];
  }

  // snapshot of the simulation state — powers the stats row and running/idle indicator
  export interface SimulationStatus {
    is_running: boolean;
    tick_count: number;
    total_orders: number;
    pending_orders: number;
    delivered_orders: number;
    active_bots: number;
  }
