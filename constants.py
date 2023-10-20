from datetime import timedelta, timezone
from enum import StrEnum, auto


DB_FOLDER = 'db_instance'
DB_PATH = f'{DB_FOLDER}/hpj_bot.db'
PERSISTENCE_PATH = f'{DB_FOLDER}/persistence'

JINJA_TEMPLATE_PATH = 'journal_view/templates'
JOURNAL_TEMPLATE = 'journal.html'

STATIC_PATH = 'static'
FLASK_PIC_PATH = f'{STATIC_PATH}/flask.png'
HEALTH_PIC_PATH = f'{STATIC_PATH}/health.png'

MSK_TIMEZONE_OFFSET = timezone(timedelta(hours=3))
ENTRY_KEY_FORMAT = '%d.%m'
TIME_FORMAT = '%H:%M%z'

ALARM_JOB_PREFIX = 'alarm'


class OutputFileFormats(StrEnum):
    HTML = auto()
    # currently under construction
    # PDF = auto()
