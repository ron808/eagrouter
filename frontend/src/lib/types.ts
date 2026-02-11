export interface Node {
    id: number;
    x: number;
    y: number;
    is_delivery_point: boolean;
    address: string;
  }

  export interface Restaurant {
    id: number;
    name: string;
    node_id: number;
    x: number;
    y: number;
    address: string;
  }

  export interface BlockedEdge {
    id: number;
    from_node_id: number;
    to_node_id: number;
  }

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

  export interface Grid {
    nodes: Node[];
    restaurants: Restaurant[];
    blocked_edges: BlockedEdge[];
    delivery_points: Node[];
  }

  export interface SimulationStatus {
    is_running: boolean;
    tick_count: number;
    total_orders: number;
    pending_orders: number;
    delivered_orders: number;
    active_bots: number;
  }
