from datetime import timedelta, timezone


DB_FOLDER = 'db_instance'
DB_PATH = f'{DB_FOLDER}/hpj_bot.db'

MSK_TIMEZONE_OFFSET = timezone(timedelta(hours=3))

ALARM_JOB_PREFIX = 'alarm'
