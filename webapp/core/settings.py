import os
from pathlib import Path

from pydantic import BaseModel
from pydantic_settings import BaseSettings

BASE_DIR = Path(os.getcwd())
DB_FOLDER = BASE_DIR / 'db_instance'


class DbSettings(BaseModel):
    url: str = f"sqlite+aiosqlite:///{DB_FOLDER}/hpj_bot.db"
    echo: bool = False


class TestDbSettings(DbSettings):
    url = f"sqlite+aiosqlite:///{DB_FOLDER}/test_db.sqlite3"
    echo = True


class AuthSettings(BaseModel):
    pub_key: bytes | str = BASE_DIR / 'certs' / 'pub_key'
    algorithm: str = 'RS256'


class Settings(BaseSettings):
    api_v1_prefix: str = "/api/v1"
    db: DbSettings = DbSettings()
    auth: AuthSettings = AuthSettings()


settings = Settings()
