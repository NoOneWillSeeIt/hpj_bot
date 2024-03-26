import os
from datetime import timedelta, timezone
from enum import StrEnum, auto
from pathlib import Path

BASE_DIR = Path(os.getcwd())
CERTS_DIR = BASE_DIR / "certs"

MSK_TIMEZONE_OFFSET = timezone(timedelta(hours=3))

DAYS_TO_STORE_ENTRIES = 60

DB_DATE_FORMAT = "%d.%m.%y"


class Channel(StrEnum):
    telegram = auto()
    # Bots from channels beneath aren't working, but shows idea behind this service
    discord = auto()
    whatsapp = auto()


class OutputFileFormats(StrEnum):
    HTML = auto()
    # currently under construction
    # PDF = auto()
