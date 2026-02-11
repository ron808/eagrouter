# test setup - spins up a sqlite db so we don't need postgres
# every test gets a clean database, no leftover state between tests

# IMPORTANT: override the db url before anything else gets imported
# otherwise sqlalchemy tries to load psycopg2 and blows up
import os
os.environ["DATABASE_URL"] = "sqlite:///./test.db"

import pytest
from unittest.mock import patch
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from app.database import Base, get_db
from app.models import Node, Restaurant, Bot, BlockedEdge
from app.models.bot import BotStatus

# sqlite, fast and disposable
TEST_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
)

# sqlite doesn't enforce foreign keys by default, this turns it on
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    # fresh tables for every single test
    # we use create_all here (not alembic) because sqlite can't handle postgres enums
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    # swap out the real db dependency with our test session
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    # patch out run_migrations so the lifespan doesn't try to run alembic on sqlite
    # also patch load_initial_data since we seed data ourselves in fixtures
    with patch("app.main.run_migrations"), \
         patch("app.main.load_initial_data"):
        # importing app here to avoid circular issues
        from app.main import app
        app.dependency_overrides[get_db] = override_get_db
        with TestClient(app) as c:
            yield c
        app.dependency_overrides.clear()


@pytest.fixture
def seed_nodes(db_session):
    # throw in a handful of nodes so the tests have something to work with
    nodes = [
        Node(id=1, x=0, y=0, is_delivery_point=False),
        Node(id=2, x=1, y=0, is_delivery_point=True),
        Node(id=3, x=2, y=0, is_delivery_point=True),
        Node(id=4, x=0, y=1, is_delivery_point=False),
        Node(id=5, x=1, y=1, is_delivery_point=False),
    ]
    db_session.add_all(nodes)
    db_session.commit()
    return nodes


@pytest.fixture
def seed_restaurant(db_session, seed_nodes):
    # one restaurant at node 1, that's all we need for most tests
    restaurant = Restaurant(id=1, name="RAMEN", node_id=1)
    db_session.add(restaurant)
    db_session.commit()
    return restaurant


@pytest.fixture
def seed_bots(db_session, seed_nodes):
    # two bots parked at node 5 (center-ish)
    bots = [
        Bot(id=1, name="Bot-1", current_node_id=5, status=BotStatus.IDLE, max_capacity=3),
        Bot(id=2, name="Bot-2", current_node_id=5, status=BotStatus.IDLE, max_capacity=3),
    ]
    db_session.add_all(bots)
    db_session.commit()
    return bots


@pytest.fixture
def seed_all(seed_nodes, seed_restaurant, seed_bots):
    # convenience fixture when you want everything
    pass
