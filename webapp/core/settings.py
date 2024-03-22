import os
from pathlib import Path

from pydantic import BaseModel
from pydantic_settings import BaseSettings

BASE_DIR = Path(os.getcwd())
WEBAPP_DIR = BASE_DIR / "webapp"
DB_FOLDER = BASE_DIR / "db_instance"
DEFAULT_URL = "localhost"
DEFAULT_REDIS_PORT = 6379


class DbSettings(BaseModel):
    url: str = f"sqlite+aiosqlite:///{DB_FOLDER.as_posix()}/hpj_bot.db"
    echo: bool = False


class TestDbSettings(DbSettings):
    url: str = f"sqlite+aiosqlite:///{DB_FOLDER.as_posix()}/test_db.sqlite3"
    echo: bool = True


class AuthSettings(BaseModel):
    pub_key: Path = BASE_DIR / "certs" / "pub_key"
    algorithm: str = "RS256"


class JinjaSettings(BaseModel):
    templates_dir: Path = (
        WEBAPP_DIR / "workers" / "reports" / "journal_view" / "templates"
    )
    journal_tmpl: str = "journal.html"


class RedisSettings(BaseModel):
    host: str = os.getenv("REDIS_URL", DEFAULT_URL)
    port: int = int(os.getenv("REDIS_PORT", DEFAULT_REDIS_PORT))
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
