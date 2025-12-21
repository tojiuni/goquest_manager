from functools import lru_cache
from pydantic import BaseSettings, validator
from typing import Dict, Any


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

    DATABASE_URL: str = None

    @validator("DATABASE_URL", pre=True, always=True)
    def assemble_db_connection(cls, v: str, values: Dict[str, Any]) -> Any:
        if isinstance(v, str):
            return v
        return (
            f"postgresql://{values.get('DB_USER')}:{values.get('DB_PASSWORD')}@"
            f"{values.get('DB_HOST')}:{values.get('DB_PORT')}/{values.get('DB_NAME')}"
        )

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings():
    return Settings()
