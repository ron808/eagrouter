# database connection setup
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
    # fastapi dependency - yields a db session and closes it after
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
    # run alembic migrations programmatically instead of using create_all()
    # this way the db schema is always managed through versioned migration files
    from sqlalchemy import inspect, text

    alembic_cfg = _get_alembic_config()
    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()

    has_alembic_version = "alembic_version" in existing_tables
    has_app_tables = "nodes" in existing_tables

    if has_app_tables and not has_alembic_version:
        # tables were created by the old create_all() approach but alembic
        # has never run before. stamp the db so alembic knows where we are,
        # then run any new migrations on top (like the triggers in 002)
        logger.info("Existing tables found without alembic history - stamping to 001...")
        command.stamp(alembic_cfg, "001")
        logger.info("Stamped. Now running any pending migrations...")
        command.upgrade(alembic_cfg, "head")
    else:
        # normal case: either fresh db or alembic is already tracking it
        logger.info("Running alembic migrations...")
        command.upgrade(alembic_cfg, "head")

    logger.info("Migrations complete")
