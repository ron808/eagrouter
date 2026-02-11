# app config - pulls from env vars with sensible defaults
from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import List


class Settings(BaseSettings):
    APP_NAME: str = "EagRoute"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    DATABASE_URL: str = "postgresql+psycopg2://eagroute:eagroute123@localhost:5432/eagroute"

    # only allowing frontend origin, learned the hard way not to use "*"
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

    TOTAL_BOTS: int = 5
    BOT_MAX_CAPACITY: int = 3
    SIMULATION_TICK_INTERVAL: float = 1.0

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
