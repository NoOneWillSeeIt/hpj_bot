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

    url: str = f"{DB_ENGINE}/{DB_FOLDER.as_posix()}/hpj_bot.db"
    echo: bool = False


class TestDbSettings(DbSettings):
    url: str = Field(
        default=f"{DB_ENGINE}/{DB_FOLDER.as_posix()}/hpj_test.db",
        validation_alias="hpj_db_test_url",
    )
    echo: bool = True


class JinjaSettings(BaseModel):
    templates_dir: Path = (
        WEBAPP_DIR / "workers" / "reports" / "journal_view" / "templates"
    )
    journal_tmpl: str = "journal.html"


class RedisSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="redis_")

    host: str = DEFAULT_URL
    port: int = DEFAULT_REDIS_PORT
    db: int = 0


class TestRedisSettings(RedisSettings):
    host: str = Field(default=DEFAULT_URL, alias='redis_test_host')
    port: int = Field(default=DEFAULT_REDIS_PORT, alias='redis_test_port')
    db: int = Field(default=1, alias='redis_test_db')


class Settings(BaseSettings):
    api_v1_prefix: str = "/api/v1"
    db: DbSettings = DbSettings()
    auth: AuthSettings = AuthSettings()
    jinja: JinjaSettings = JinjaSettings()
    redis: RedisSettings = RedisSettings()
    entry_store_days: int = 60


settings = Settings()


def init_test_settings():
    settings.db = TestDbSettings()
    settings.redis = TestRedisSettings()
