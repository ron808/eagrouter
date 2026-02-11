// Interactive map visualization (assignment requirement).
// Renders the grid with nodes, restaurants (food emojis), delivery houses, and animated bots.
// Each cell shows what's currently on it — a bot, a restaurant, a delivery house, or just an empty node.
"use client";
import type { BlockedEdge, Bot, Node, Restaurant } from "@/lib/types";

type StackPos = { x: number; y: number };

// Multiple bots can occupy the same cell at once (e.g. two idle bots at origin).
// These layouts define how to arrange 1-5 bots inside a single cell so they
// don't overlap — think of it like a little formation pattern per count.
const BOT_STACK_LAYOUTS: Record<number, StackPos[]> = {
  1: [{ x: 0, y: 0 }],

  2: [
    { x: -0.5, y: 0 },
    { x: 0.5, y: 0 },
  ],

  3: [
    { x: 0, y: -0.6 },
    { x: -0.5, y: 0.4 },
    { x: 0.5, y: 0.4 },
  ],

  4: [
    { x: -0.5, y: -0.5 },
    { x: 0.5, y: -0.5 },
    { x: -0.5, y: 0.5 },
    { x: 0.5, y: 0.5 },
  ],

  // 5 is also the fallback for 6+ bots (we just show the first 5)
  5: [
    { x: -0.5, y: -0.5 },
    { x: 0.5, y: -0.5 },
    { x: -0.5, y: 0.5 },
    { x: 0.5, y: 0.5 },
    { x: 0, y: 0 },
  ],
};

export type GridProps = {
  nodes: Node[];
  restaurants: Restaurant[];
  blockedEdges: BlockedEdge[];
  bots: Bot[];
  cellSize?: number; // allow parent to control cell size
};

// map restaurant name to a food emoji — makes the grid more visual and fun
const RESTAURANT_EMOJI: Record<string, string> = {
  RAMEN: "\u{1F35C}",
  CURRY: "\u{1F35B}",
  PIZZA: "\u{1F355}",
  SUSHI: "\u{1F363}",
};

const BOT_COLORS = [
  "#7c6bf5", // purple
  "#3b82f6", // blue
  "#f472b6", // pink
  "#22d3ee", // cyan
  "#fb923c", // orange
];

export default function Grid({
  nodes,
  restaurants,
  blockedEdges,
  bots,
  cellSize = 56,
}: GridProps) {
  void blockedEdges; // not rendered yet but accepted as a prop for future use
  const CELL = cellSize;

  // figure out the grid boundaries from node coordinates
  const xs = nodes.map((n) => n.x);
  const ys = nodes.map((n) => n.y);
  const minX = xs.length ? Math.min(...xs) : 0;
  const maxX = xs.length ? Math.max(...xs) : 0;
  const minY = ys.length ? Math.min(...ys) : 0;
  const maxY = ys.length ? Math.max(...ys) : 0;

  // build quick lookup maps so we don't scan arrays repeatedly while rendering
  const nodeByXY = new Map<string, Node>();
  for (const n of nodes) nodeByXY.set(`${n.x},${n.y}`, n);

  const restaurantByNodeId = new Map<number, Restaurant>();
  for (const r of restaurants) restaurantByNodeId.set(r.node_id, r);

  // group bots by node so we can stack them if multiple bots are on the same cell
  const botsByNodeId = new Map<number, Bot[]>();
  for (const b of bots) {
    const existing = botsByNodeId.get(b.current_node_id) || [];
    existing.push(b);
    botsByNodeId.set(b.current_node_id, existing);
  }

  // build a 2D array of rows for rendering — null means empty/no-node cell
  const rows: Array<Array<Node | null>> = [];
  for (let y = minY; y <= maxY; y++) {
    const row: Array<Node | null> = [];
    for (let x = minX; x <= maxX; x++)
      row.push(nodeByXY.get(`${x},${y}`) ?? null);
    rows.push(row);
  }

  // scale bot circles and emoji sizes relative to the cell size so it looks good at any zoom
  const botSingle = Math.round(CELL * 0.6);
  const botStacked = Math.round(CELL * 0.4);
  const fontSingle = Math.round(CELL * 0.25);
  const fontStacked = Math.round(CELL * 0.18);

  return (
    <div className="shrink-0">
      <div
        className="grid gap-[3px]"
        style={{
          gridTemplateColumns: `28px repeat(${
            maxX - minX + 1
          }, ${CELL}px) 28px`,
        }}
      >
        {/* top-left empty corner */}
        <div />
        {/* x-axis labels */}
        {Array.from({ length: maxX - minX + 1 }).map((_, i) => (
          <div
            key={`col-${i}`}
            className="text-center text-[10px] font-mono pb-1"
            style={{ color: "var(--text-muted)" }}
          >
            {minX + i}
          </div>
        ))}
        <div />

        {rows.flatMap((row, rowIdx) => [
          /* y-axis label left */
          <div
            key={`yl-${rowIdx}`}
            className="text-right pr-1.5 self-center text-[10px] font-mono"
            style={{ color: "var(--text-muted)" }}
          >
            {minY + rowIdx}
          </div>,

          ...row.map((node, colIdx) => {
            if (!node) {
              return (
                <div
                  key={`e-${rowIdx}-${colIdx}`}
                  className="rounded-md"
                  style={{
                    width: CELL,
                    height: CELL,
                    background: "#0b0b12",
                    border: "1px solid #13131c",
                  }}
                />
              );
            }

            const isDelivery = node.is_delivery_point;
            const restaurant = restaurantByNodeId.get(node.id);
            const nodeBots = botsByNodeId.get(node.id) || [];
            const hasBot = nodeBots.length > 0;

            // pick cell background and border based on what's sitting on this node
            let bg = "var(--bg-elevated)";
            let border = "var(--border-subtle)";
            if (hasBot) {
              const color =
                BOT_COLORS[(nodeBots[0].id - 1) % BOT_COLORS.length];
              bg = `${color}15`;
              border = `${color}50`;
            } else if (restaurant) {
              bg = "rgba(251, 146, 60, 0.06)";
              border = "rgba(251, 146, 60, 0.2)";
            } else if (isDelivery) {
              bg = "rgba(52, 211, 153, 0.05)";
              border = "rgba(52, 211, 153, 0.15)";
            }

            return (
              <div
                key={node.id}
                className="relative rounded-md flex items-center justify-center bot-cell"
                style={{
                  width: CELL,
                  height: CELL,
                  background: bg,
                  border: `1px solid ${border}`,
                }}
                title={`${node.address} (${node.x},${node.y})${
                  restaurant ? ` - ${restaurant.name}` : ""
                }${isDelivery ? " - Delivery Point" : ""}${
                  hasBot ? ` - ${nodeBots.map((b) => b.name).join(", ")}` : ""
                }`}
              >
                {hasBot ? (
                  <div className="relative w-full h-full">
                    {(
                      BOT_STACK_LAYOUTS[nodeBots.length] || BOT_STACK_LAYOUTS[5]
                    ).map((pos, i) => {
                      const bot = nodeBots[i];
                      if (!bot) return null;

                      const color =
                        BOT_COLORS[(bot.id - 1) % BOT_COLORS.length];
                      const isActive = bot.status !== "IDLE";

                      const size = nodeBots.length > 1 ? botStacked : botSingle;

                      return (
                        <div
                          key={bot.id}
                          className={`absolute flex items-center justify-center rounded-full text-white font-bold ${
                            isActive ? "bot-active" : ""
                          }`}
                          style={{
                            width: size,
                            height: size,
                            fontSize:
                              nodeBots.length > 1 ? fontStacked : fontSingle,
                            background: color,
                            boxShadow: `0 0 10px ${color}70`,
                            left: "50%",
                            top: "50%",
                            transform: `translate(
              calc(-50% + ${pos.x * size}px),
              calc(-50% + ${pos.y * size}px)
            )`,
                          }}
                        >
                          {bot.id}
                        </div>
                      );
                    })}
                  </div>
                ) : restaurant ? (
                  <span
                    style={{ fontSize: Math.round(CELL * 0.4), lineHeight: 1 }}
                  >
                    {RESTAURANT_EMOJI[restaurant.name] || "\u{1F374}"}
                  </span>
                ) : isDelivery ? (
                  <span
                    style={{
                      fontSize: Math.round(CELL * 0.32),
                      lineHeight: 1,
                      opacity: 0.7,
                    }}
                  >
                    {"\u{1F3E0}"}
                  </span>
                ) : (
                  <span
                    className="w-1 h-1 rounded-full"
                    style={{ background: "var(--border)" }}
                  />
                )}
              </div>
            );
          }),

          /* y-axis label right */
          <div
            key={`yr-${rowIdx}`}
            className="pl-1.5 self-center text-[10px] font-mono"
            style={{ color: "var(--text-muted)" }}
          >
            {minY + rowIdx}
          </div>,
        ])}
      </div>

      {/* legend */}
      <div
        className="flex gap-4 mt-3 justify-center text-[11px]"
        style={{ color: "var(--text-muted)" }}
      >
        <span className="flex items-center gap-1">{"\u{1F3E0}"} House</span>
        <span className="flex items-center gap-1">
          {"\u{1F355}"} Restaurant
        </span>
        <span className="flex items-center gap-1">
          <span
            className="w-3.5 h-3.5 rounded-full flex items-center justify-center text-white text-[8px] font-bold"
            style={{ background: BOT_COLORS[0] }}
          >
            1
          </span>
          Bot
        </span>
      </div>
    </div>
  );
}
