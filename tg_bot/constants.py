import os
from datetime import timedelta, timezone
from enum import StrEnum, auto
from pathlib import Path

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings


BASE_DIR = Path(os.getcwd())
BOT_PATH = BASE_DIR / "tg_bot"


# PATHS
PERSISTENCE_PATH = BASE_DIR / "persistence"
STATIC_PATH = BASE_DIR / "static"
FLASK_PIC_PATH = STATIC_PATH / "flask.png"
HEALTH_PIC_PATH = STATIC_PATH / "health.png"

# TIME
MSK_TIMEZONE_OFFSET = timezone(timedelta(hours=3))
ENTRY_KEY_FORMAT = "%d.%m"
TIME_FORMAT = "%H:%M%z"


class BotSettings(BaseSettings):
    developer_chat_id: str = Field(default='', validation_alias=AliasChoices('DEVELOPER_CHAT_ID'))
    token: str = Field(default='', validation_alias=AliasChoices('HPJ_TOKEN'))
    test_token: str = Field(default='', validation_alias=AliasChoices('HPJ_TEST_TOKEN'))
    test_chat: str = Field(default='', validation_alias=AliasChoices('HPJ_TEST_CHAT'))
    remote_url: str = Field(default='', validation_alias=AliasChoices('HPJ_REMOTE_URL'))


class OutputFileFormats(StrEnum):
    HTML = auto()
    # currently under construction
    # PDF = auto()


bot_settings = BotSettings()


def init_remote_settings(remote_url: str):
    global bot_settings
    settings_dump = bot_settings.model_dump()
    settings_dump['remote_url'] = remote_url
    bot_settings = BotSettings(**settings_dump)
