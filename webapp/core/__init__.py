from webapp.core.settings import settings
from webapp.core.db_helper import DatabaseHelper

db_helper = DatabaseHelper(settings.db_url, settings.db_echo)
