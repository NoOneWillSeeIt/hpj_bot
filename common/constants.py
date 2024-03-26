import os
from enum import StrEnum, auto
from pathlib import Path

BASE_DIR = Path(os.getcwd())
CERTS_DIR = BASE_DIR / "certs"


class Channel(StrEnum):
    telegram = auto()
    # Bots from channels beneath aren't working, but shows idea behind this service
    discord = auto()
    whatsapp = auto()


class OutputFileFormats(StrEnum):
    HTML = auto()
    # currently under construction
    # PDF = auto()
