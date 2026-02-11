// I am using this API client to communicate with our FastAPI backend.
// Instead of complex WebSockets, I decided to go with simple polling (setInterval in page.tsx). (reasoning behind that is simple results, and not a production grade project at this point)
// This approach is more robust for our current needs and ensures we get near real-time 
// updates for bot positions and order statuses every second without overcomplicating the stack.

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";

// I've added a helper function here to handle response validation. 
// It's important that we catch backend errors (like rate limits or server issues) early 
// so the UI doesn't try to render invalid or empty data.
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
