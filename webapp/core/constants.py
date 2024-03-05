from enum import StrEnum, auto


class Channel(StrEnum):
    telegram = auto()
    # Bots from channels beneath aren't working, but shows idea behind this service
    discord = auto()
    whatsapp = auto()


class ReportTaskProducer(StrEnum):
    channel = auto()
    scheduler = auto()
