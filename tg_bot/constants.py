from pathlib import Path

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

    certfile: Path = CERTS_DIR / "ssl-cert.pem"
    key: Path = CERTS_DIR / "ssl-key.key"


class WebappSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="hpj_remote_")

    url: str = ""
    api_endpoint: str = "api/v1"


class BotSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="hpj_")

    developer_chat_id: str = ""
    token: str = ""
    test_token: str = ""
    test_chat: str = ""
    remote: WebappSettings = WebappSettings()
    ssl: SslSettings = SslSettings()
    auth: AuthSettings = AuthSettings()


bot_settings = BotSettings()
