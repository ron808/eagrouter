# db connection and migration setup — all schema changes go through alembic migrations, not create_all()
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from alembic.config import Config
from alembic import command
from app.config import settings

logger = logging.getLogger("eagroute")

engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
    echo=False,
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

Base = declarative_base()


def get_db():
    # fastapi dependency — gives you a db session and auto-closes it when the request is done
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _get_alembic_config():
    import os
    alembic_ini = os.path.join(os.path.dirname(os.path.dirname(__file__)), "alembic.ini")
    alembic_cfg = Config(alembic_ini)
    alembic_cfg.set_main_option("sqlalchemy.url", settings.DATABASE_URL)
    return alembic_cfg


def run_migrations():
    # run alembic migrations on startup so the db schema stays in sync with our versioned migration files
    from sqlalchemy import inspect, text

    alembic_cfg = _get_alembic_config()
    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()

    has_alembic_version = "alembic_version" in existing_tables
    has_app_tables = "nodes" in existing_tables

    if has_app_tables and not has_alembic_version:
        # tables exist but alembic hasn't tracked them yet — stamp to 001 so alembic knows where we are, then run any new migrations
        logger.info("Existing tables found without alembic history - stamping to 001...")
        command.stamp(alembic_cfg, "001")
        logger.info("Stamped. Now running any pending migrations...")
        command.upgrade(alembic_cfg, "head")
    else:
        # normal path: fresh db or alembic is already tracking things
        logger.info("Running alembic migrations...")
        command.upgrade(alembic_cfg, "head")

    logger.info("Migrations complete")
