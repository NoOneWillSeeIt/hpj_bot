from datetime import timedelta, timezone
from enum import StrEnum, auto
import os


# PATHS
DB_FOLDER = 'db_instance'
DB_PATH = f'{DB_FOLDER}/hpj_bot.db'
TEST_DB_PATH = f'{DB_FOLDER}/test_hpj_bot.db'
PERSISTENCE_PATH = f'{DB_FOLDER}/persistence'

JINJA_TEMPLATE_PATH = 'journal_view/templates'
JOURNAL_TEMPLATE = 'journal.html'

STATIC_PATH = 'static'
FLASK_PIC_PATH = f'{STATIC_PATH}/flask.png'
HEALTH_PIC_PATH = f'{STATIC_PATH}/health.png'

# TIME
MSK_TIMEZONE_OFFSET = timezone(timedelta(hours=3))
ENTRY_KEY_FORMAT = '%d.%m'
TIME_FORMAT = '%H:%M%z'

# JOBS
ALARM_JOB_PREFIX = 'alarm'
DAYS_TO_STORE = 60
DAYS_TO_STORE_BACKUP = 30

# TOKENS/IDS
DEVELOPER_CHAT_ID = os.environ.get('DEVELOPER_CHAT_ID')
HPJ_BOT_TOKEN = os.environ.get('HPJ_TOKEN')
TEST_TOKEN = os.environ.get('HPJ_TEST_TOKEN')
TEST_CHAT_ID = os.environ.get('HPJ_TEST_CHAT')


class OutputFileFormats(StrEnum):
    HTML = auto()
    # currently under construction
    # PDF = auto()
