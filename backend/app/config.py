from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    api_token: str = ""
    database_url: str = "sqlite:///./app.db"
    redis_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/1"

    data_home: str = "/data"
    tdl_home: str = "/data/.tdl"
    download_dir: str = "/data/downloads"

    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    celery_task_soft_time_limit: int = 82800
    celery_task_time_limit: int = 86400

    @property
    def cors_origin_list(self) -> List[str]:
        raw = self.cors_origins.strip()
        if raw == "*":
            return ["*"]
        return [o.strip() for o in raw.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
