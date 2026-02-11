# loads initial data from CSV files into the database on startup
# reads from sample_data.csv (nodes, restaurants, delivery points) and BlockedPaths.csv (blocked edges)

import csv
import os
from sqlalchemy.orm import Session
from app.config import settings
from app.models import Node, Restaurant, Bot, BlockedEdge
from app.models.bot import BotStatus

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data")


def load_nodes(db: Session) -> int:
    # loads grid nodes from sample_data.csv -- each row has id, x, y, and whether it's a valid delivery point
    existing_count = db.query(Node).count()
    if existing_count > 0:
        print(f"  Nodes already loaded ({existing_count})")
        return 0

    csv_path = os.path.join(DATA_DIR, "sample_data.csv")

    if not os.path.exists(csv_path):
        print(f"  CSV file not found: {csv_path}")
        return 0

    nodes_loaded = 0

    with open(csv_path, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)

        for row in reader:
            # Mapping the coordinate system to an address - for example: LR74
            node = Node(
                id=int(row["id"]),
                x=int(row["x"]),
                y=int(row["y"]),
                is_delivery_point=row["delivery_point"].strip().upper() == "TRUE"
            )
            db.add(node)
            nodes_loaded += 1

    db.commit()
    print(f"  Loaded {nodes_loaded} nodes")
    return nodes_loaded


def load_restaurants(db: Session) -> int:
    # reads sample_data.csv and creates a restaurant wherever a column (RAMEN, CURRY, etc.) is TRUE
    existing_count = db.query(Restaurant).count()
    if existing_count > 0:
        print(f"  Restaurants already loaded ({existing_count})")
        return 0

    csv_path = os.path.join(DATA_DIR, "sample_data.csv")

    if not os.path.exists(csv_path):
        print(f"  CSV file not found: {csv_path}")
        return 0

    restaurant_columns = ["RAMEN", "CURRY", "PIZZA", "SUSHI"]
    restaurants_loaded = 0

    with open(csv_path, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)

        for row in reader:
            node_id = int(row["id"])

            for restaurant_name in restaurant_columns:
                if row[restaurant_name].strip().upper() == "TRUE":
                    restaurant = Restaurant(
                        name=restaurant_name,
                        node_id=node_id
                    )
                    db.add(restaurant)
                    restaurants_loaded += 1
                    print(f"    {restaurant_name} at node {node_id}")

    db.commit()
    print(f"  Loaded {restaurants_loaded} restaurants")
    return restaurants_loaded


def load_blocked_edges(db: Session) -> int:
    # loads blocked edges from BlockedPaths.csv -- these are paths bots can't travel through
    existing_count = db.query(BlockedEdge).count()
    if existing_count > 0:
        print(f"  Blocked edges already loaded ({existing_count})")
        return 0

    csv_path = os.path.join(DATA_DIR, "BlockedPaths.csv")

    if not os.path.exists(csv_path):
        print(f"  CSV file not found: {csv_path}")
        return 0

    edges_loaded = 0

    with open(csv_path, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)

        for row in reader:
            edge = BlockedEdge(
                from_node_id=int(row["from_id"]),
                to_node_id=int(row["to_id"])
            )
            db.add(edge)
            edges_loaded += 1

    db.commit()
    print(f"  Loaded {edges_loaded} blocked edges")
    return edges_loaded


def create_bots(db: Session, num_bots: int = 5) -> int:
    # Bot endpoints for managing fleet capacity and status
    existing_count = db.query(Bot).count()
    if existing_count > 0:
        print(f"  Bots already created ({existing_count})")
        return 0

    # bots start at the central station (4,3)
    center_node = db.query(Node).filter(Node.x == 4, Node.y == 3).first()

    if not center_node:
        center_node = db.query(Node).first()

    start_node_id = center_node.id if center_node else None

    bots_created = 0

    for i in range(1, num_bots + 1):
        bot = Bot(
            name=f"Bot-{i}",
            current_node_id=start_node_id,
            status=BotStatus.IDLE,
            max_capacity=settings.MAX_BOT_CAPACITY
        )
        db.add(bot)
        bots_created += 1
        print(f"    Created {bot.name} at node {start_node_id}")

    db.commit()
    print(f"  Created {bots_created} bots")
    return bots_created


def load_initial_data(db: Session) -> dict:
    # safe to call multiple times -- skips anything that's already been loaded
    print("Loading initial data...")

    print("  Loading nodes...")
    nodes = load_nodes(db)

    print("  Loading restaurants...")
    restaurants = load_restaurants(db)

    print("  Loading blocked edges...")
    blocked = load_blocked_edges(db)

    print("  Creating bots...")
    bots = create_bots(db)

    print("Initial data loading complete.")

    return {
        "nodes_loaded": nodes,
        "restaurants_loaded": restaurants,
        "blocked_edges_loaded": blocked,
        "bots_created": bots
    }
