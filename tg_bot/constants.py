from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from common.constants import BASE_DIR, CERTS_DIR, AuthSettings

BOT_PATH = BASE_DIR / "tg_bot"


# PATHS
PERSISTENCE_PATH = BOT_PATH / "persistence"
STATIC_PATH = BOT_PATH / "static"
FLASK_PIC_PATH = STATIC_PATH / "flask.png"
HEALTH_PIC_PATH = STATIC_PATH / "health.png"


class SslSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="ssl_")

    certfile: Path = Field(
        default=CERTS_DIR / "ssl-cert.pem",
        validation_alias="cert_path",
    )
    key: Path = Field(
        default=CERTS_DIR / "ssl-key.key",
        validation_alias="key_path",
    )


class BotSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="hpj_")

    developer_chat_id: str = Field(default="", validation_alias="developer_chat_id")
    token: str = Field(default="", validation_alias="token")
    test_token: str = Field(default="", validation_alias="test_token")
    test_chat: str = Field(default="", validation_alias="test_chat")
    remote_url: str = Field(default="", validation_alias="remote_url")
    ssl: SslSettings = SslSettings()
    auth: AuthSettings = AuthSettings()


bot_settings = BotSettings()


def init_remote_settings(remote_url: str):
    global bot_settings
    settings_dump = bot_settings.model_dump()
    settings_dump["remote_url"] = remote_url
    bot_settings = BotSettings(**settings_dump)
