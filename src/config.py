from functools import lru_cache
from pydantic import model_validator
from pydantic_settings import BaseSettings
from typing import Any, Optional


class Settings(BaseSettings):
    PLANE_API_BASE_URL: str
    PLANE_API_KEY: str
    LOG_LEVEL: str = "info"

    # Database settings
    DB_HOST: str
    DB_PORT: str
    DB_USER: str
    DB_PASSWORD: str
    DB_NAME: str

    DATABASE_URL: Optional[str] = None


    @model_validator(mode='after')
    def assemble_db_connection(self) -> "Settings":
        if isinstance(self.DATABASE_URL, str):
            return self
        self.DATABASE_URL = (
            f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@"
            f"{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )
        return self

    class Config:
        extra = "ignore"
        env_file = ".env"


@lru_cache()
def get_settings():
    return Settings()
