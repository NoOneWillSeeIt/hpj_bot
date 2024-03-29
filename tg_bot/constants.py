from pathlib import Path

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings

from common.constants import BASE_DIR, CERTS_DIR

BOT_PATH = BASE_DIR / "tg_bot"


# PATHS
PERSISTENCE_PATH = BOT_PATH / "persistence"
STATIC_PATH = BOT_PATH / "static"
FLASK_PIC_PATH = STATIC_PATH / "flask.png"
HEALTH_PIC_PATH = STATIC_PATH / "health.png"


class SslSettings(BaseSettings):
    certfile: Path = Field(
        default=CERTS_DIR / "ssl-cert.pem",
        validation_alias=AliasChoices("SSL_CERT_PATH"),
    )
    key: Path = Field(
        default=CERTS_DIR / "ssl-key.key",
        validation_alias=AliasChoices("SSL_KEY_PATH"),
    )


class BotSettings(BaseSettings):
    developer_chat_id: str = Field(
        default="", validation_alias=AliasChoices("DEVELOPER_CHAT_ID")
    )
    token: str = Field(default="", validation_alias=AliasChoices("HPJ_TOKEN"))
    test_token: str = Field(default="", validation_alias=AliasChoices("HPJ_TEST_TOKEN"))
    test_chat: str = Field(default="", validation_alias=AliasChoices("HPJ_TEST_CHAT"))
    remote_url: str = Field(default="", validation_alias=AliasChoices("HPJ_REMOTE_URL"))
    ssl: SslSettings = SslSettings()


bot_settings = BotSettings()


def init_remote_settings(remote_url: str):
    global bot_settings
    settings_dump = bot_settings.model_dump()
    settings_dump["remote_url"] = remote_url
    bot_settings = BotSettings(**settings_dump)
