from functools import lru_cache
from pydantic import field_validator, ValidationInfo
from pydantic_settings import BaseSettings
from typing import Any


class Settings(BaseSettings):
    PLANE_API_BASE_URL: str
    PLANE_API_KEY: str
    PLANE_WORKSPACE_SLUG: str
    LOG_LEVEL: str = "info"

    # Database settings
    DB_HOST: str
    DB_PORT: str
    DB_USER: str
    DB_PASSWORD: str
    DB_NAME: str

    DATABASE_URL: str

    @field_validator("DATABASE_URL", mode="before")
    def assemble_db_connection(cls, v: str, info: ValidationInfo) -> Any:
        if isinstance(v, str):
            return v
        if not info.data:
            return v
        return (
            f"postgresql://{info.data.get('DB_USER')}:{info.data.get('DB_PASSWORD')}@"
            f"{info.data.get('DB_HOST')}:{info.data.get('DB_PORT')}/{info.data.get('DB_NAME')}"
        )

    class Config:
        extra = "ignore"
        env_file = ".env"


@lru_cache()
def get_settings():
    return Settings()
