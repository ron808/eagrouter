const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";

// helper that checks the response before parsing json
// if the backend returns an error (rate limit, 500, etc) we throw instead
// of silently passing garbage data to the UI
async function safeFetch(url: string, options?: RequestInit) {
  const res = await fetch(url, options);
  if (!res.ok) {
    const body = await res.text();
    throw new Error(`API error ${res.status}: ${body}`);
  }
  return res.json();
}

export const api = {
  getGrid: () => safeFetch(API_BASE + "/grid"),
  getBots: () => safeFetch(API_BASE + "/bots"),
  getBotPositions: () => safeFetch(API_BASE + "/simulation/bots/positions"),
  getOrders: () => safeFetch(API_BASE + "/orders"),
  createOrder: (restaurantId: number, deliveryNodeId: number) =>
    safeFetch(API_BASE + "/orders", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ restaurant_id: restaurantId, delivery_node_id: deliveryNodeId })
    }),
  getStatus: () => safeFetch(API_BASE + "/simulation/status"),
  start: () => safeFetch(API_BASE + "/simulation/start", { method: "POST" }),
  stop: () => safeFetch(API_BASE + "/simulation/stop", { method: "POST" }),
  reset: () => safeFetch(API_BASE + "/simulation/reset", { method: "POST" }),
  tick: () => safeFetch(API_BASE + "/simulation/tick", { method: "POST" }),
};
