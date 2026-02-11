"use client";
import { useEffect, useState, useRef, useCallback, useMemo } from "react";
import { api } from "@/lib/api";
import { Grid as GridType, Bot, Order, SimulationStatus } from "@/lib/types";
import Grid from "@/components/Grid";

// ─── bot color palette (matches Grid.tsx) ────────────────────────────
const BOT_COLORS = ["#7c6bf5", "#3b82f6", "#f472b6", "#22d3ee", "#fb923c"];

// ─── panel widths (desktop only) ─────────────────────────────────────
const LEFT_W = 300;
const RIGHT_W = 370;
const COMPACT_BREAKPOINT = 1100; // below this → single column

// ─── tiny reusable components ────────────────────────────────────────
function Dot({ color, pulse }: { color: string; pulse?: boolean }) {
  return (
    <span
      className={pulse ? "blink" : ""}
      style={{
        display: "inline-block",
        width: 8,
        height: 8,
        borderRadius: "50%",
        background: color,
        boxShadow: `0 0 6px ${color}90`,
      }}
    />
  );
}

function Kbd({ children }: { children: React.ReactNode }) {
  return (
    <kbd
      style={{
        padding: "1px 6px",
        borderRadius: 4,
        background: "var(--bg-input)",
        border: "1px solid var(--border)",
        fontSize: 11,
        fontFamily: "var(--font-geist-mono), monospace",
        color: "var(--text-secondary)",
      }}
    >
      {children}
    </kbd>
  );
}

// ─── status badge ────────────────────────────────────────────────────
const STATUS_STYLES: Record<string, { bg: string; text: string; border: string }> = {
  DELIVERED:  { bg: "rgba(52,211,153,0.10)",  text: "var(--green)",      border: "rgba(52,211,153,0.25)" },
  PICKED_UP:  { bg: "rgba(251,191,36,0.10)",  text: "var(--amber)",      border: "rgba(251,191,36,0.25)" },
  ASSIGNED:   { bg: "rgba(96,165,250,0.10)",   text: "var(--blue)",       border: "rgba(96,165,250,0.25)" },
  PENDING:    { bg: "rgba(136,136,160,0.08)",  text: "var(--text-muted)", border: "rgba(136,136,160,0.15)" },
  CANCELLED:  { bg: "rgba(248,113,113,0.10)",  text: "var(--red)",        border: "rgba(248,113,113,0.25)" },
};

function Badge({ status }: { status: string }) {
  const s = STATUS_STYLES[status] || STATUS_STYLES.PENDING;
  return (
    <span style={{ padding: "2px 8px", borderRadius: 6, fontSize: 11, fontWeight: 500, background: s.bg, color: s.text, border: `1px solid ${s.border}`, whiteSpace: "nowrap" }}>
      {status}
    </span>
  );
}

// ─── card wrapper ────────────────────────────────────────────────────
function Card({ children, title, hint, style: extraStyle }: { children: React.ReactNode; title?: string; hint?: string; style?: React.CSSProperties }) {
  return (
    <div style={{ background: "var(--bg-card)", border: "1px solid var(--border)", borderRadius: 14, padding: "14px 16px", ...extraStyle }}>
      {title && (
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 12 }}>
          <h2 style={{ fontSize: 12, fontWeight: 600, color: "var(--text-secondary)", letterSpacing: "0.02em", textTransform: "uppercase" }}>{title}</h2>
          {hint && <span style={{ fontSize: 11, color: "var(--text-muted)" }}>{hint}</span>}
        </div>
      )}
      {children}
    </div>
  );
}

// ─── button component ────────────────────────────────────────────────
function Btn({ onClick, label, color, disabled }: { onClick: () => void; label: string; color: string; disabled?: boolean }) {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      style={{
        padding: "7px 16px", borderRadius: 8, fontSize: 13, fontWeight: 500,
        border: `1px solid ${disabled ? "var(--border)" : `${color}35`}`,
        background: disabled ? "var(--bg-input)" : `${color}12`,
        color: disabled ? "var(--text-muted)" : color,
        cursor: disabled ? "not-allowed" : "pointer",
        opacity: disabled ? 0.5 : 1,
        transition: "all 0.15s ease",
      }}
    >
      {label}
    </button>
  );
}

// ─── shared section renderers (used in both layouts) ─────────────────

function SimControlsContent({ isRunning, autoRun, setAutoRun, handleStart, handleStop, handleTick, handleReset }: {
  isRunning: boolean; autoRun: boolean; setAutoRun: (v: boolean) => void;
  handleStart: () => void; handleStop: () => void; handleTick: () => void; handleReset: () => void;
}) {
  return (
    <>
      <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
        <Btn onClick={handleStart} disabled={isRunning} color="var(--green)" label="▶ Start" />
        <Btn onClick={handleStop} disabled={!isRunning} color="var(--red)" label="⏹ Stop" />
        <Btn onClick={handleTick} color="var(--accent)" label="→ Tick" />
        <Btn onClick={handleReset} color="var(--text-muted)" label="↺ Reset" />
      </div>
      <label style={{
        display: "flex", alignItems: "center", gap: 6, padding: "7px 12px", borderRadius: 8, marginTop: 10,
        background: autoRun ? "rgba(124,107,245,0.12)" : "var(--bg-input)",
        border: `1px solid ${autoRun ? "rgba(124,107,245,0.3)" : "var(--border)"}`,
        cursor: "pointer", fontSize: 13,
        color: autoRun ? "var(--accent)" : "var(--text-secondary)",
        userSelect: "none", transition: "all 0.15s ease",
      }}>
        <input type="checkbox" checked={autoRun} onChange={(e) => setAutoRun(e.target.checked)} style={{ accentColor: "var(--accent)", margin: 0 }} />
        Auto-tick every second
      </label>
    </>
  );
}

function NewOrderContent({ grid, selectedRestaurant, setSelectedRestaurant, selectedDelivery, setSelectedDelivery, handleCreate }: {
  grid: GridType; selectedRestaurant: number; setSelectedRestaurant: (v: number) => void;
  selectedDelivery: number; setSelectedDelivery: (v: number) => void; handleCreate: () => void;
}) {
  const selectStyle: React.CSSProperties = { width: "100%", padding: "8px 10px", borderRadius: 8, background: "var(--bg-input)", border: "1px solid var(--border)", color: "var(--text)", fontSize: 13, outline: "none" };
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
      <div>
        <label style={{ fontSize: 11, color: "var(--text-muted)", display: "block", marginBottom: 4 }}>Restaurant</label>
        <select value={selectedRestaurant} onChange={(e) => setSelectedRestaurant(Number(e.target.value))} style={selectStyle}>
          {grid.restaurants.map((r) => <option key={r.id} value={r.id}>{r.name} — {r.address}</option>)}
        </select>
      </div>
      <div>
        <label style={{ fontSize: 11, color: "var(--text-muted)", display: "block", marginBottom: 4 }}>Deliver to</label>
        <select value={selectedDelivery} onChange={(e) => setSelectedDelivery(Number(e.target.value))} style={selectStyle}>
          {grid.delivery_points.map((d) => <option key={d.id} value={d.id}>{d.address}</option>)}
        </select>
      </div>
      <button onClick={handleCreate} style={{ width: "100%", padding: "9px 0", borderRadius: 8, background: "var(--accent)", color: "#fff", fontWeight: 600, fontSize: 13, border: "none", cursor: "pointer", boxShadow: "0 2px 12px rgba(124,107,245,0.3)" }}>
        + Create Order
      </button>
    </div>
  );
}

function BotsContent({ bots }: { bots: Bot[] }) {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
      {bots.map((b) => {
        const color = BOT_COLORS[(b.id - 1) % BOT_COLORS.length];
        const active = b.status !== "IDLE";
        return (
          <div key={b.id} style={{ display: "flex", alignItems: "center", gap: 10, padding: "8px 10px", borderRadius: 8, background: active ? `${color}0d` : "var(--bg-elevated)", border: `1px solid ${active ? `${color}30` : "var(--border-subtle)"}`, transition: "all 0.3s ease" }}>
            <div style={{ width: 28, height: 28, borderRadius: "50%", display: "flex", alignItems: "center", justifyContent: "center", fontWeight: 700, fontSize: 12, color: "#fff", background: active ? color : "var(--bg-input)", boxShadow: active ? `0 0 10px ${color}50` : "none", flexShrink: 0 }}>
              {active ? b.id : <span style={{ color: "var(--text-muted)" }}>{b.id}</span>}
            </div>
            <div style={{ flex: 1, minWidth: 0 }}>
              <div style={{ fontSize: 12, fontWeight: 600, color: active ? "var(--text)" : "var(--text-muted)" }}>
                {b.name}
                <span style={{ fontWeight: 400, fontSize: 10, color: "var(--text-muted)", marginLeft: 6, fontFamily: "var(--font-geist-mono), monospace" }}>({b.x},{b.y})</span>
              </div>
              <div style={{ fontSize: 10, color: active ? color : "var(--text-muted)", marginTop: 1 }}>
                {b.status}
                {b.active_orders > 0 && <span style={{ marginLeft: 6, color: "var(--text-secondary)" }}>{b.active_orders}/3 orders</span>}
                {b.target?.action && <span style={{ marginLeft: 6, color: "var(--text-secondary)" }}>· {b.target.action === "pickup" ? "⬆ Pickup" : "⬇ Deliver"} #{b.target.order_id}</span>}
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}

function StatsRow({ status }: { status: SimulationStatus }) {
  return (
    <div style={{ display: "flex", gap: 10, flexWrap: "wrap", justifyContent: "center" }}>
      {[
        { label: "Total", value: status.total_orders, color: "var(--text)" },
        { label: "Pending", value: status.pending_orders, color: "var(--text-muted)" },
        { label: "Active", value: status.total_orders - status.pending_orders - status.delivered_orders, color: "var(--blue)" },
        { label: "Delivered", value: status.delivered_orders, color: "var(--green)" },
      ].map((s) => (
        <div key={s.label} style={{ padding: "8px 18px", borderRadius: 8, background: "var(--bg-card)", border: "1px solid var(--border)", textAlign: "center", minWidth: 70 }}>
          <div style={{ fontSize: 18, fontWeight: 700, fontFamily: "var(--font-geist-mono), monospace", color: s.color }}>{s.value}</div>
          <div style={{ fontSize: 10, color: "var(--text-muted)", marginTop: 2 }}>{s.label}</div>
        </div>
      ))}
    </div>
  );
}

function OrdersList({ filteredOrders, orders, orderFilter, setOrderFilter }: {
  filteredOrders: Order[]; orders: Order[];
  orderFilter: "ALL" | "ACTIVE" | "DELIVERED"; setOrderFilter: (v: "ALL" | "ACTIVE" | "DELIVERED") => void;
}) {
  return (
    <>
      <div style={{ display: "flex", gap: 4, marginBottom: 10, flexShrink: 0 }}>
        {(["ALL", "ACTIVE", "DELIVERED"] as const).map((f) => (
          <button key={f} onClick={() => setOrderFilter(f)} style={{
            padding: "4px 12px", borderRadius: 6, fontSize: 11, fontWeight: 500,
            border: "1px solid transparent", cursor: "pointer",
            background: orderFilter === f ? "var(--bg-input)" : "transparent",
            color: orderFilter === f ? "var(--text)" : "var(--text-muted)",
            borderColor: orderFilter === f ? "var(--border)" : "transparent",
            transition: "all 0.15s ease",
          }}>{f}</button>
        ))}
      </div>
      <div style={{ flex: 1, overflowY: "auto", display: "flex", flexDirection: "column", gap: 5 }}>
        {filteredOrders.length === 0 ? (
          <p style={{ fontSize: 12, color: "var(--text-muted)", textAlign: "center", padding: "20px 0" }}>
            {orders.length === 0 ? "No orders yet — create one to get started!" : "No orders match this filter."}
          </p>
        ) : (
          filteredOrders.map((o) => (
            <div key={o.id} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "8px 10px", borderRadius: 8, background: "var(--bg-elevated)", border: "1px solid var(--border-subtle)", flexShrink: 0 }}>
              <div style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 12, minWidth: 0, overflow: "hidden" }}>
                <span style={{ fontFamily: "var(--font-geist-mono), monospace", color: "var(--text-muted)", fontSize: 10, flexShrink: 0 }}>#{o.id}</span>
                <span style={{ color: "var(--text)", fontWeight: 500, whiteSpace: "nowrap" }}>{o.restaurant_name}</span>
                <span style={{ color: "var(--text-muted)" }}>→</span>
                <span style={{ color: "var(--text-secondary)", fontFamily: "var(--font-geist-mono), monospace", fontSize: 11, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{o.delivery_address}</span>
                {o.bot_name && (
                  <span style={{ padding: "1px 6px", borderRadius: 5, fontSize: 10, fontWeight: 600, flexShrink: 0, background: `${BOT_COLORS[((o.bot_id ?? 1) - 1) % BOT_COLORS.length]}18`, color: BOT_COLORS[((o.bot_id ?? 1) - 1) % BOT_COLORS.length], border: `1px solid ${BOT_COLORS[((o.bot_id ?? 1) - 1) % BOT_COLORS.length]}30` }}>
                    {o.bot_name}
                  </span>
                )}
              </div>
              <Badge status={o.status} />
            </div>
          ))
        )}
      </div>
    </>
  );
}

// ─── main app ────────────────────────────────────────────────────────
export default function Home() {
  const [grid, setGrid] = useState<GridType | null>(null);
  const [bots, setBots] = useState<Bot[]>([]);
  const [orders, setOrders] = useState<Order[]>([]);
  const [status, setStatus] = useState<SimulationStatus | null>(null);
  const [selectedRestaurant, setSelectedRestaurant] = useState<number>(0);
  const [selectedDelivery, setSelectedDelivery] = useState<number>(0);
  const [autoRun, setAutoRun] = useState(false);
  const [showGuide, setShowGuide] = useState(true);
  const [orderFilter, setOrderFilter] = useState<"ALL" | "ACTIVE" | "DELIVERED">("ALL");
  const [windowSize, setWindowSize] = useState({ w: 1400, h: 900 });

  const logRef = useRef<HTMLDivElement>(null);
  const [logs, setLogs] = useState<string[]>([]);
  const [toast, setToast] = useState<{ msg: string; type: "error" | "info" } | null>(null);

  const compact = windowSize.w < COMPACT_BREAKPOINT;

  useEffect(() => {
    const update = () => setWindowSize({ w: window.innerWidth, h: window.innerHeight });
    update();
    window.addEventListener("resize", update);
    return () => window.removeEventListener("resize", update);
  }, []);

  const log = useCallback((msg: string) => {
    setLogs((prev) => [...prev, `${new Date().toLocaleTimeString()} — ${msg}`]);
  }, []);

  useEffect(() => { api.getGrid().then((g) => { setGrid(g); if (g.restaurants.length) setSelectedRestaurant(g.restaurants[0].id); if (g.delivery_points.length) setSelectedDelivery(g.delivery_points[0].id); }); }, []);

  useEffect(() => {
    let alive = true;
    const poll = async () => { if (!alive) return; try { const [b, o, s] = await Promise.all([api.getBotPositions(), api.getOrders(), api.getStatus()]); if (!alive) return; setBots(b.bots || []); setOrders(o); setStatus(s); } catch (e) { console.error(e); } };
    poll(); const id = setInterval(poll, 1000); return () => { alive = false; clearInterval(id); };
  }, []);

  useEffect(() => { if (!autoRun) return; const id = setInterval(() => api.tick(), 1000); return () => clearInterval(id); }, [autoRun]);
  useEffect(() => { if (logRef.current) logRef.current.scrollTop = logRef.current.scrollHeight; }, [logs]);
  useEffect(() => { if (!toast) return; const id = setTimeout(() => setToast(null), 5000); return () => clearTimeout(id); }, [toast]);

  const handleCreate = async () => {
    if (!selectedRestaurant || !selectedDelivery) return;
    try {
      await api.createOrder(selectedRestaurant, selectedDelivery);
      const rName = grid?.restaurants.find((r) => r.id === selectedRestaurant)?.name ?? "";
      log(`Order created — ${rName} → delivery node ${selectedDelivery}`);
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : "Failed to create order";
      // extract the detail from the JSON body if present
      const detailMatch = msg.match(/"detail"\s*:\s*"([^"]+)"/);
      setToast({ msg: detailMatch ? detailMatch[1] : msg, type: "error" });
      log(`Order failed — ${detailMatch ? detailMatch[1] : msg}`);
    }
  };
  const handleStart = async () => { await api.start(); log("Simulation started"); };
  const handleStop  = async () => { await api.stop(); setAutoRun(false); log("Simulation stopped"); };
  const handleReset = async () => { await api.reset(); setAutoRun(false); setLogs([]); log("Simulation reset"); };
  const handleTick  = async () => { await api.tick(); };

  const filteredOrders = orders.filter((o) => {
    if (orderFilter === "ACTIVE") return o.status !== "DELIVERED" && o.status !== "CANCELLED";
    if (orderFilter === "DELIVERED") return o.status === "DELIVERED";
    return true;
  });

  // compute optimal cell size based on available space
  const cellSize = useMemo(() => {
    if (!grid) return 56;
    const xs = grid.nodes.map((n) => n.x);
    const ys = grid.nodes.map((n) => n.y);
    const cols = xs.length ? Math.max(...xs) - Math.min(...xs) + 1 : 10;
    const rows = ys.length ? Math.max(...ys) - Math.min(...ys) + 1 : 10;
    if (compact) {
      // in compact mode, grid takes full width with some padding
      const availW = windowSize.w - 80;
      const maxByW = Math.floor(availW / (cols + 0.5));
      return Math.max(32, Math.min(64, maxByW));
    }
    const centerW = windowSize.w - LEFT_W - RIGHT_W - 80;
    const centerH = windowSize.h - 140;
    const maxByW = Math.floor(centerW / (cols + 0.5));
    const maxByH = Math.floor(centerH / (rows + 1.5));
    return Math.max(40, Math.min(80, Math.min(maxByW, maxByH)));
  }, [grid, windowSize, compact]);

  if (!grid) {
    return (
      <div style={{ height: "100vh", display: "flex", alignItems: "center", justifyContent: "center" }}>
        <span style={{ color: "var(--text-muted)", animation: "soft-pulse 2s ease-in-out infinite" }}>Loading grid…</span>
      </div>
    );
  }

  const isRunning = status?.is_running ?? false;
  const topH = 48 + (showGuide ? 42 : 0);
  const panelMaxH = `calc(100vh - ${topH}px)`;

  // ═══════════════════════════════════════════════════════════════════
  // SHARED: toast, header + guide banner (identical in both layouts)
  // ═══════════════════════════════════════════════════════════════════
  const toastEl = toast ? (
    <div style={{
      position: "fixed", top: 16, left: "50%", transform: "translateX(-50%)",
      zIndex: 9999, padding: "10px 20px", borderRadius: 10,
      background: toast.type === "error" ? "rgba(248,113,113,0.15)" : "rgba(96,165,250,0.15)",
      border: `1px solid ${toast.type === "error" ? "rgba(248,113,113,0.4)" : "rgba(96,165,250,0.4)"}`,
      color: toast.type === "error" ? "var(--red)" : "var(--blue)",
      fontSize: 13, fontWeight: 500, display: "flex", alignItems: "center", gap: 10,
      backdropFilter: "blur(12px)", boxShadow: "0 4px 24px rgba(0,0,0,0.4)",
      maxWidth: "90vw",
    }}>
      <span>{toast.msg}</span>
      <button onClick={() => setToast(null)} style={{ background: "none", border: "none", color: "inherit", cursor: "pointer", fontSize: 16, lineHeight: 1, padding: "0 2px", opacity: 0.7 }}>×</button>
    </div>
  ) : null;

  const headerEl = (
    <header style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: compact ? "10px 16px" : "10px 24px", borderBottom: "1px solid var(--border)", background: "var(--bg-card)", flexShrink: 0, height: 48, boxSizing: "border-box" }}>
      <div style={{ display: "flex", alignItems: "center", gap: compact ? 8 : 16 }}>
        <h1 style={{ fontSize: compact ? 18 : 20, fontWeight: 700, letterSpacing: "-0.02em", margin: 0 }}>
          <span style={{ color: "var(--accent)" }}>Eag</span>Route
        </h1>
        {!compact && <span style={{ fontSize: 12, color: "var(--text-muted)" }}>Autonomous delivery bot simulation</span>}
      </div>
      <div style={{ display: "flex", alignItems: "center", gap: 10, padding: "6px 14px", borderRadius: 8, background: "var(--bg-elevated)", border: "1px solid var(--border)", fontSize: 12 }}>
        <Dot color={isRunning ? "var(--green)" : "var(--text-muted)"} pulse={isRunning} />
        <span style={{ color: isRunning ? "var(--green)" : "var(--text-muted)", fontWeight: 500 }}>{isRunning ? "Running" : "Idle"}</span>
        {status && (
          <>
            <span style={{ color: "var(--border)", margin: "0 2px" }}>|</span>
            <span style={{ fontFamily: "var(--font-geist-mono), monospace", color: "var(--text-secondary)" }}>Tick {status.tick_count}</span>
          </>
        )}
      </div>
    </header>
  );

  const guideEl = showGuide ? (
    <div style={{ background: "var(--accent-glow)", borderBottom: "1px solid rgba(124,107,245,0.2)", padding: compact ? "8px 16px" : "8px 24px", display: "flex", alignItems: "center", gap: 12, flexShrink: 0, minHeight: 42, boxSizing: "border-box" }}>
      <span style={{ fontSize: 12, fontWeight: 600, color: "var(--accent)", whiteSpace: "nowrap" }}>Quick start:</span>
      <span style={{ fontSize: 12, color: "var(--text-secondary)", lineHeight: 1.5, overflow: "hidden", whiteSpace: "nowrap", textOverflow: "ellipsis" }}>
        <strong>1.</strong> Create order → <Kbd>+ Order</Kbd>
        &nbsp;&nbsp;<strong>2.</strong> <Kbd>▶ Start</Kbd> or <Kbd>→ Tick</Kbd>
        &nbsp;&nbsp;<strong>3.</strong> Watch bots
        &nbsp;&nbsp;<strong>4.</strong> <Kbd>Auto</Kbd> for continuous ticking
      </span>
      <button onClick={() => setShowGuide(false)} style={{ background: "none", border: "none", color: "var(--text-muted)", cursor: "pointer", fontSize: 16, lineHeight: 1, padding: "2px 6px", marginLeft: "auto", flexShrink: 0 }} aria-label="Dismiss guide">×</button>
    </div>
  ) : null;

  const logEl = (
    <Card title="Activity Log" hint={`${logs.length}`}>
      <div ref={logRef} style={{ maxHeight: 120, overflowY: "auto", padding: 8, borderRadius: 6, background: "var(--bg)", fontFamily: "var(--font-geist-mono), monospace", fontSize: 11, lineHeight: 1.7, color: "var(--text-muted)" }}>
        {logs.length === 0 ? <span style={{ fontStyle: "italic" }}>Actions will appear here…</span> : logs.map((entry, i) => <div key={i}>{entry}</div>)}
      </div>
    </Card>
  );

  // ═══════════════════════════════════════════════════════════════════
  // COMPACT LAYOUT (single-column, scrollable)
  // ═══════════════════════════════════════════════════════════════════
  if (compact) {
    return (
      <main style={{ minHeight: "100vh", display: "flex", flexDirection: "column" }}>
        {toastEl}
        {headerEl}
        {guideEl}
        <div style={{ flex: 1, overflowY: "auto", padding: 16, display: "flex", flexDirection: "column", gap: 14 }}>
          {/* controls row: sim + new order side by side */}
          <div style={{ display: "flex", gap: 14, flexWrap: "wrap" }}>
            <Card title="Simulation" style={{ flex: 1, minWidth: 260 }}>
              <SimControlsContent isRunning={isRunning} autoRun={autoRun} setAutoRun={setAutoRun} handleStart={handleStart} handleStop={handleStop} handleTick={handleTick} handleReset={handleReset} />
            </Card>
            <Card title="New Order" hint="Pick & create" style={{ flex: 1, minWidth: 260 }}>
              <NewOrderContent grid={grid} selectedRestaurant={selectedRestaurant} setSelectedRestaurant={setSelectedRestaurant} selectedDelivery={selectedDelivery} setSelectedDelivery={setSelectedDelivery} handleCreate={handleCreate} />
            </Card>
          </div>

          {/* grid centered */}
          <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 14 }}>
            <Grid nodes={grid.nodes} restaurants={grid.restaurants} blockedEdges={grid.blocked_edges} bots={bots} cellSize={cellSize} />
            {status && <StatsRow status={status} />}
          </div>

          {/* orders + bots + log */}
          <Card title={`Orders (${filteredOrders.length})`} hint={orders.length === 0 ? "Create your first order above ↑" : undefined}>
            <OrdersList filteredOrders={filteredOrders} orders={orders} orderFilter={orderFilter} setOrderFilter={setOrderFilter} />
          </Card>

          <div style={{ display: "flex", gap: 14, flexWrap: "wrap" }}>
            <Card title="Bots" hint={`${bots.filter((b) => b.status !== "IDLE").length} active`} style={{ flex: 1, minWidth: 260 }}>
              <BotsContent bots={bots} />
            </Card>
            <div style={{ flex: 1, minWidth: 260 }}>{logEl}</div>
          </div>
        </div>
      </main>
    );
  }

  // ═══════════════════════════════════════════════════════════════════
  // DESKTOP LAYOUT (3-column, viewport-locked)
  // ═══════════════════════════════════════════════════════════════════
  return (
    <main style={{ height: "100vh", display: "flex", flexDirection: "column", overflow: "hidden" }}>
      {toastEl}
      {headerEl}
      {guideEl}

      <div style={{ flex: 1, display: "flex", overflow: "hidden" }}>
        {/* LEFT PANEL */}
        <aside style={{ width: LEFT_W, flexShrink: 0, borderRight: "1px solid var(--border)", padding: 14, display: "flex", flexDirection: "column", gap: 12, overflowY: "auto", maxHeight: panelMaxH }}>
          <Card title="Simulation">
            <SimControlsContent isRunning={isRunning} autoRun={autoRun} setAutoRun={setAutoRun} handleStart={handleStart} handleStop={handleStop} handleTick={handleTick} handleReset={handleReset} />
          </Card>
          <Card title="New Order" hint="Pick & create">
            <NewOrderContent grid={grid} selectedRestaurant={selectedRestaurant} setSelectedRestaurant={setSelectedRestaurant} selectedDelivery={selectedDelivery} setSelectedDelivery={setSelectedDelivery} handleCreate={handleCreate} />
          </Card>
          <Card title="Bots" hint={`${bots.filter((b) => b.status !== "IDLE").length} active`}>
            <BotsContent bots={bots} />
          </Card>
          {logEl}
        </aside>

        {/* CENTER */}
        <section style={{ flex: 1, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", padding: 16, overflow: "auto", minWidth: 0 }}>
          <Grid nodes={grid.nodes} restaurants={grid.restaurants} blockedEdges={grid.blocked_edges} bots={bots} cellSize={cellSize} />
          {status && <div style={{ marginTop: 14 }}><StatsRow status={status} /></div>}
        </section>

        {/* RIGHT PANEL */}
        <aside style={{ width: RIGHT_W, flexShrink: 0, borderLeft: "1px solid var(--border)", display: "flex", flexDirection: "column", overflow: "hidden", maxHeight: panelMaxH }}>
          <div style={{ flex: 1, padding: 14, display: "flex", flexDirection: "column", overflow: "hidden" }}>
            <Card title={`Orders (${filteredOrders.length})`} hint={orders.length === 0 ? "Create your first order ←" : undefined} style={{ flex: 1, display: "flex", flexDirection: "column", overflow: "hidden" }}>
              <OrdersList filteredOrders={filteredOrders} orders={orders} orderFilter={orderFilter} setOrderFilter={setOrderFilter} />
            </Card>
          </div>
        </aside>
      </div>
    </main>
  );
}
