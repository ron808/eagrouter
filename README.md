# EagRoute

Route optimization delivery bot system. Full-stack app for managing autonomous food delivery bots on a 9x9(10x10 actually) grid map.

## Quick start

```bash
docker-compose up --build
```

That's it. Three services spin up:
- **Frontend** at http://localhost:3000
- **Backend API** at http://localhost:8000
- **Swagger docs** at http://localhost:8000/docs

To stop: `docker-compose down`
To reset the database: `docker-compose down -v`

## What this does

- 9x9 grid with 79 nodes, 4 restaurants, 14 delivery houses, 19 blocked paths
- 5 delivery bots, each carries up to 3 orders
- A* pathfinding that avoids blocked edges
- Greedy bot assignment (closest available bot gets the order)
- Tick-based simulation with real-time map visualization
- Address format: L(i,j) e.g. Pizza = LR74

## Project structure

```
eagroute/
├── docker-compose.yml
├── backend/                  # FastAPI + SQLAlchemy + PostgreSQL
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── models/           # Node, Restaurant, Bot, Order, BlockedEdge
│   │   ├── schemas/          # Pydantic request/response models
│   │   ├── routers/          # grid, bots, orders, simulation
│   │   └── services/         # A* pathfinding, simulation engine
│   └── alembic/              # database migrations
├── frontend/                 # Next.js + React + Tailwind
│   └── src/
│       ├── app/page.tsx      # main dashboard
│       ├── components/       # Grid map component
│       └── lib/              # api client, types
└── data/
    ├── sample_data.csv
    └── BlockedPaths.csv
```

## Tech stack

**Backend:** FastAPI, SQLAlchemy, PostgreSQL, Alembic, Pydantic

**Frontend:** Next.js 16, React 19, TypeScript, Tailwind CSS

## Order lifecycle

PENDING -> ASSIGNED -> PICKED_UP -> DELIVERED

Orders can be cancelled while PENDING or ASSIGNED.

## API endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | /api/grid | Full map data |
| GET | /api/bots | All bots + status |
| GET | /api/orders | All orders |
| POST | /api/orders | Create order |
| PUT | /api/orders/{id} | Update order |
| DELETE | /api/orders/{id} | Cancel order |
| POST | /api/simulation/start | Start sim |
| POST | /api/simulation/stop | Stop sim |
| POST | /api/simulation/tick | Advance 1 tick |
| POST | /api/simulation/reset | Reset everything |

## Development

```bash
# view logs
docker-compose logs -f

# backend logs only
docker-compose logs -f backend

# connect to database
docker-compose exec db psql -U eagroute -d eagroute
```
