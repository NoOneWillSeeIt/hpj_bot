from pydantic import BaseModel
from pydantic_settings import BaseSettings


class DbSettings(BaseModel):
    url: str = f"sqlite+aiosqlite:///db.sqlite3"
    echo: bool = False


class TestDbSettings:
    url = f"sqlite+aiosqlite:///test_db.sqlite3"
    echo = True


class Settings(BaseSettings):
    api_v1_prefix: str = "/api/v1"
    db_url: str = f"sqlite+aiosqlite:///test_db.sqlite3"
    db_echo: bool = True


settings = Settings()
