from pathlib import Path

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from common.constants import BASE_DIR, AuthSettings

WEBAPP_DIR = BASE_DIR / "webapp"
DB_FOLDER = BASE_DIR / "db_instance"
DEFAULT_URL = "localhost"
DEFAULT_REDIS_PORT = 6379


class DbSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="hpj_db_")

    url: str = f"{DB_FOLDER.as_posix()}/hpj_bot.db"
    dialect: str = "sqlite"
    async_driver: str = "+aiosqlite"
    driver: str = ""
    echo: bool = False
    _engine_url_tmpl = "{}{}:///{}"

    @property
    def engine_url(self) -> str:
        return self._engine_url_tmpl.format(self.dialect, self.driver, self.url)

    @property
    def async_engine_url(self) -> str:
        return self._engine_url_tmpl.format(self.dialect, self.async_driver, self.url)


class TestDbSettings(DbSettings):
    url: str = Field(
        default=f"{DB_FOLDER.as_posix()}/hpj_test.db",
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
    host: str = Field(default=DEFAULT_URL, alias="redis_test_host")
    port: int = Field(default=DEFAULT_REDIS_PORT, alias="redis_test_port")
    db: int = Field(default=1, alias="redis_test_db")


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
