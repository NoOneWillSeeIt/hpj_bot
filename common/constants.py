import os
from datetime import timedelta, timezone
from enum import StrEnum, auto
from pathlib import Path
from typing import Final

BASE_DIR = Path(os.getcwd())
CERTS_DIR = BASE_DIR / "certs"

MSK_TIMEZONE_OFFSET = timezone(timedelta(hours=3))

DAYS_TO_STORE_ENTRIES = 60

ENTRY_DATE_FORMAT = "%d.%m.%Y"


class Channel(StrEnum):
    telegram = auto()
    # Bots from channels beneath aren't working, but shows idea behind this service
    discord = auto()
    whatsapp = auto()


class OutputFileFormats(StrEnum):
    HTML = auto()
    # currently under construction
    # PDF = auto()


class AuthSettings:
    public_key_path: Final[Path] = CERTS_DIR / "public.key"
    private_key_path: Final[Path] = CERTS_DIR / "private.key"
    public_key: Final[bytes] = public_key_path.read_bytes()
    private_key: Final[bytes] = private_key_path.read_bytes()
    algorithm: Final[str] = "RS256"
    expire_seconds: Final[int] = 5 * 60
