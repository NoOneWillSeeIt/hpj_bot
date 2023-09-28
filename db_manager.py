
from datetime import time
import json
import logging
import sqlite3


def get_db_conn_from_bot_data(bot_data: dict) -> sqlite3.Connection:
    try:
        conn = bot_data['db_conn']
        conn.cursor()
    except Exception as ex:
        logging.warning(f'DB was dead. Trying to restore. ex: {ex}')
        conn = sqlite3.connect(bot_data['db_path'])
        bot_data['db_conn'] = conn
        
    return conn


async def awaitable_execute(cursor: sqlite3.Cursor, sql: str, params: dict):
    return cursor.execute(sql, params)


async def db_write_alarm(bot_data: dict, chat_id: int, time: time):
    conn = get_db_conn_from_bot_data(bot_data)
    await awaitable_execute(
        conn.cursor(), 
        '''
        INSERT INTO journal(chat_id, alarm) VALUES(:chat_id, :alarm)
        ON CONFLICT(chat_id) DO UPDATE SET alarm = excluded.alarm;
        ''', 
        {'chat_id': chat_id, 'alarm': time.strftime('%H:%M%z')})
    conn.commit()


async def db_write_entry(bot_data: dict, chat_id: int, entry: dict):
    conn = get_db_conn_from_bot_data(bot_data)
    date = entry.get('q_date')
    await awaitable_execute(
        conn.cursor(), 
        f'''
        INSERT INTO journal(chat_id, entries) VALUES(:chat_id, json_object(:date, :entry))
        ON CONFLICT(chat_id) DO UPDATE SET entries = json_set(coalesce(entries, '{{}}'), '$."{date}"', :entry);
        ''', 
        {'chat_id': chat_id, 
         'date': date, 
         'entry': json.dumps(entry, ensure_ascii=False)})
    conn.commit()
