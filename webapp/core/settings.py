from pathlib import Path

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from common.constants import BASE_DIR, AuthSettings

WEBAPP_DIR = BASE_DIR / "webapp"
DB_FOLDER = BASE_DIR / "db_instance"
DB_ENGINE = "sqlite+aiosqlite://"
DEFAULT_URL = "localhost"
DEFAULT_REDIS_PORT = 6379


class DbSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="hpj_db_")

    url: str = Field(
        default=f"{DB_ENGINE}/{DB_FOLDER.as_posix()}/hpj_bot.db",
        validation_alias="url",
    )
    echo: bool = False


class TestDbSettings(DbSettings):
    url: str = Field(
        default=f"{DB_ENGINE}/{DB_FOLDER.as_posix()}/hpj_test.db",
        validation_alias="test_url",
    )
    echo: bool = True


class JinjaSettings(BaseModel):
    templates_dir: Path = (
        WEBAPP_DIR / "workers" / "reports" / "journal_view" / "templates"
    )
    journal_tmpl: str = "journal.html"


class RedisSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="redis_")

    host: str = Field(default=DEFAULT_URL, validation_alias="url")
    port: int = Field(default=DEFAULT_REDIS_PORT, validation_alias="port")
    db: int = 0


class TestRedisSettings(RedisSettings):
    host: str = DEFAULT_URL
    port: int = DEFAULT_REDIS_PORT
    db: int = 0


class Settings(BaseSettings):
    api_v1_prefix: str = "/api/v1"
    db: DbSettings = DbSettings()
    auth: AuthSettings = AuthSettings()
    jinja: JinjaSettings = JinjaSettings()
    redis: RedisSettings = RedisSettings()
    entry_store_days: int = 60


settings = Settings()


def init_test_settings():
    global settings
    settings = Settings(db=TestDbSettings(), redis=TestRedisSettings())
