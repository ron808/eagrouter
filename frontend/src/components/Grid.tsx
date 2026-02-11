"use client";
import type { BlockedEdge, Bot, Node, Restaurant } from "@/lib/types";

// This is our main interactive map visualization.
// I've built this to render the grid, placing nodes, restaurants, delivery houses, and bots in their correct positions.
// Each cell is dynamic, showing the most relevant information based on what's currently located there.

type StackPos = { x: number; y: number };

// I noticed that multiple bots often occupy the same cell, especially at the starting hub.
// To prevent them from overlapping and becoming unclickable, I've defined several formations here.
// These layouts arrange 1 to 5 bots in a clear, visible pattern within a single cell.
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

// I've mapped each restaurant category to a specific food emoji.
// This adds a bit of visual flair to the grid and helps users identify pickup points quickly.
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

  // First, I am determining the boundaries of our grid by looking at the min/max 
  // coordinates among all provided nodes. This allows the map to scale dynamically 
  // if the grid size changes in the backend.
  const xs = nodes.map((n) => n.x);
  const ys = nodes.map((n) => n.y);
  const minX = xs.length ? Math.min(...xs) : 0;
  const maxX = xs.length ? Math.max(...xs) : 0;
  const minY = ys.length ? Math.min(...ys) : 0;
  const maxY = ys.length ? Math.max(...ys) : 0;

  // I am building lookup maps here for nodes, restaurants, and bots. 
  // This is a performance optimization that allows us to find what belongs in 
  // each grid cell in O(1) time during the main render loop.
  const nodeByXY = new Map<string, Node>();
  for (const n of nodes) nodeByXY.set(`${n.x},${n.y}`, n);

  const restaurantByNodeId = new Map<number, Restaurant>();
  for (const r of restaurants) restaurantByNodeId.set(r.node_id, r);

  // Grouping bots by node is essential for our stacking logic when multiple 
  // bots are at the same location.
  const botsByNodeId = new Map<number, Bot[]>();
  for (const b of bots) {
    const existing = botsByNodeId.get(b.current_node_id) || [];
    existing.push(b);
    botsByNodeId.set(b.current_node_id, existing);
  }

  // I am transforming our node list into a proper 2D grid structure.
  // This makes it much easier to iterate through rows and columns when rendering 
  // the CSS grid layout.
  const rows: Array<Array<Node | null>> = [];
  for (let y = minY; y <= maxY; y++) {
    const row: Array<Node | null> = [];
    for (let x = minX; x <= maxX; x++)
      row.push(nodeByXY.get(`${x},${y}`) ?? null);
    rows.push(row);
  }

  // To ensure the UI remains visually balanced, I'm scaling the icons and fonts
  // based on our dynamic cell size. This ensures the bots look good whether 
  // we're on a large monitor or a compact screen.
  const botSingle = Math.round(CELL * 0.6);
  const botStacked = Math.round(CELL * 0.4);
  const fontSingle = Math.round(CELL * 0.25);
  const fontStacked = Math.round(CELL * 0.18);

  return (
    <div className="shrink-0">
      <div
        className="grid gap-[3px]"
        style={{
          gridTemplateColumns: `28px repeat(${maxX - minX + 1
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
            } else if (node.x === 4 && node.y === 3) {
              // Bot Station styling
              bg = "rgba(124, 107, 245, 0.08)";
              border = "rgba(124, 107, 245, 0.3)";
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
                title={`${node.address} (${node.x},${node.y})${restaurant ? ` - ${restaurant.name}` : ""
                  }${isDelivery ? " - Delivery Point" : ""}${hasBot ? ` - ${nodeBots.map((b) => b.name).join(", ")}` : ""
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
                          className={`absolute flex items-center justify-center rounded-full text-white font-bold ${isActive ? "bot-active" : ""
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
                ) : node.x === 4 && node.y === 3 ? (
                  <span
                    style={{
                      fontSize: Math.round(CELL * 0.35),
                      lineHeight: 1,
                      color: "var(--accent)",
                      opacity: 0.8,
                    }}
                  >
                    {"\u{1F6F0}"}
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
        <span className="flex items-center gap-1">
          <span
            className="w-2.5 h-2.5 rounded-sm"
            style={{
              background: "rgba(124, 107, 245, 0.15)",
              border: "1px solid rgba(124, 107, 245, 0.4)",
            }}
          />
          Bot Station
        </span>
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
