from datetime import datetime
import json
import unittest

import aiosqlite
from constants import MSK_TIMEZONE_OFFSET, TIME_FORMAT

import db_queries


class DbCrudOpsTest(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self) -> None:
        self.conn = await aiosqlite.connect(':memory:')
        await self.conn.execute('''
            CREATE TABLE journal(chat_id BIGINT PRIMARY KEY, entries TEXT, alarm TEXT);
        ''')
        await self.conn.commit()
        self.bot_data = {
            'db_conn': self.conn,
            'db_path': ':memory:',
        }

    async def test_get_db_conn(self):
        conn = await db_queries.get_db_conn_from_bot_data({'db_conn': self.conn})
        self.assertIs(self.conn, conn)
        conn = await db_queries.get_db_conn_from_bot_data({'db_path': ':memory:'})
        self.assertTrue(conn.is_alive())

    async def test_write_alarm(self):
        time = datetime.now(tz=MSK_TIMEZONE_OFFSET).timetz()
        time = time.replace(second=0, microsecond=0)
        for msg in ['write alarm first time', 'overwrite existing alarm']:
            await db_queries.write_alarm(self.bot_data, 1, time)
            cur = await self.conn.execute('''
                select alarm from journal where chat_id = 1
            ''')
            res = await cur.fetchone()
            self.assertTrue(len(res) > 0, msg)
            self.assertEqual(time,
                             datetime.strptime(res[0], TIME_FORMAT).timetz(),
                             msg)

    async def test_clear_alarm(self):
        time = datetime.now().timetz()
        await db_queries.write_alarm(self.bot_data, 1, time)
        for msg in ['clear existing alarm', 'clear non existing alarm']:
            await db_queries.clear_alarm(self.bot_data, 1)
            cur = await self.conn.execute('''
                select alarm from journal where chat_id = 1
            ''')
            res = await cur.fetchone()
            self.assertTrue(len(res) > 0, msg)
            self.assertIsNone(res[0], msg)

    async def test_write_entries(self):
        key = '23.04'
        data = {'sample': 'text'}
        for msg in ['write new entry', 'overwrite existing entry']:
            await db_queries.write_entry(self.bot_data, 1, key, data)
            cur = await self.conn.execute('select entries from journal where chat_id = 1')
            res = await cur.fetchone()
            parsed_entries = json.loads(res[0])
            self.assertTrue(isinstance(parsed_entries[key], dict), msg)
            self.assertEqual(parsed_entries[key], data, msg)

            data['sample'] = 'text2'

    async def test_read_entries(self):
        key = '23.04'
        data = {'sample': 'text'}
        expected = {}
        for msg in ['read non existing entry', 'read existing entry']:
            entries = await db_queries.read_entries(self.bot_data, 1)
            self.assertTrue(isinstance(entries, dict), msg)
            self.assertEqual(entries, expected, msg)

            await db_queries.write_entry(self.bot_data, 1, key, data)
            expected = {key: data}
