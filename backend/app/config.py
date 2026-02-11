# app config — pulls from env vars, falls back to sensible defaults for local dev
from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import List


class Settings(BaseSettings):
    APP_NAME: str = "EagRoute"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    DATABASE_URL: str = "postgresql+psycopg2://eagroute:eagroute123@localhost:5432/eagroute"

    # CORS — only allowing our frontend origin, don't use "*" or you'll regret it
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

    # assignment spec: 5 bots with max 3 orders each
    TOTAL_BOTS: int = 5
    BOT_MAX_CAPACITY: int = 3
    # how often the simulation loop ticks (in seconds)
    SIMULATION_TICK_INTERVAL: float = 1.0

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
