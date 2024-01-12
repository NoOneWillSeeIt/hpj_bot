from datetime import datetime, timedelta
import json
import sqlite3
from unittest import TestCase
from constants import DAYS_TO_STORE_BACKUP

from db import queries as syncdb
from tests.utils.common import create_test_sync_db


class SyncDBTestCase(TestCase):

    def setUp(self) -> None:
        db_path, conn = create_test_sync_db()
        self.conn = conn
        self.db_path = db_path
        return super().setUp()

    def tearDown(self) -> None:
        self.conn.close()
        return super().tearDown()

    def test_check_table_exists(self):
        cases = [(True, 'table should exist'), (False, 'table shouldn\'t exist')]
        for should_exist, msg in cases:
            with self.subTest(msg):
                if not should_exist:
                    self.conn.execute('''
                        DROP TABLE journal
                    ''')
                    self.conn.commit()

                tbl_exists = syncdb.check_table_exists(self.conn, 'journal')
                self.assertEqual(tbl_exists, should_exist)

    def write_entry(self, chat_id: int, key: str, data: dict):
        self.conn.execute(
            '''
            INSERT INTO journal(chat_id, entries)
            VALUES
            (
                :chat_id,
                json_object(
                    :key,
                    json(:entry)
                )
            ) ON CONFLICT(chat_id) DO
            UPDATE
            SET
            entries = json_set(
                coalesce(entries, '{}'),
                '$.' || '"' || :key || '"',
                json(:entry)
            );
            ''',
            {
                'chat_id': chat_id,
                'key': key,
                'entry': json.dumps(data, ensure_ascii=False)
            }
        )
        self.conn.commit()

    def test_read_entries(self):
        chat_id = 1
        key = '23.04'
        data = {'sample': 'text'}

        self.write_entry(chat_id, key, data)

        entries = syncdb.read_entries(self.db_path, chat_id)
        self.assertTrue(isinstance(entries[key], dict))
        self.assertEqual(entries[key], data)

        entries = syncdb.read_entries(self.db_path)

    def test_read_entries_keys(self):
        chat_id = 1
        data = {'sample': 'text'}
        keys = ['23.04', '24.04', '25.04']

        for key in keys:
            self.write_entry(chat_id, key, data)

        db_keys = syncdb.read_entries_keys(self.db_path, chat_id)
        self.assertEqual(set(keys), db_keys)

    def test_mark_entries_for_delete(self):
        chat_id = 1
        data = {'sample': 'text'}
        keys = ['23.04', '24.04', '25.04']
        non_existing_keys = ['31.05, 30.02']
        keys_to_del = ['23.04', '24.04']
        keys_to_save = list(set(keys) - set(keys_to_del))

        for key in keys:
            self.write_entry(chat_id, key, data)

        syncdb.mark_entries_for_delete(self.db_path, chat_id, keys_to_del + non_existing_keys)

        cursor = self.conn.execute('''
            select * from journal where chat_id = :chat_id
        ''', {'chat_id': chat_id})

        cursor.row_factory = sqlite3.Row
        results = cursor.fetchone()
        entries = json.loads(results['entries'])
        self.assertEqual(set(entries.keys()), set(keys_to_save))

        cursor = self.conn.execute('''
            select entries from del_journal where chat_id = :chat_id
        ''', {'chat_id': chat_id})

        del_entries = json.loads(cursor.fetchone()[0])
        self.assertTrue(isinstance(del_entries, dict))
        self.assertTrue(len(del_entries) > 0)
        self.assertEqual(set(keys_to_del), set(del_entries.keys()))

    def test_delete_outdated_entries(self):
        chat_id = 1
        data = {'sample': 'text'}
        cur_date = datetime.now()
        keys = [cur_date - timedelta(days=DAYS_TO_STORE_BACKUP+i) for i in range(1, 5)]
        keys_to_del = [keys[0], keys[1]]

        for key in keys:
            self.write_entry(chat_id, key, data)

        syncdb.mark_entries_for_delete(self.db_path, chat_id, keys_to_del)
        syncdb.delete_marked_entries(self.db_path, chat_id)

        cursor = self.conn.execute('''
            select *
            from del_journal
            where chat_id = :chat_id
        ''', {'chat_id': chat_id})

        cursor.row_factory = sqlite3.Row
        results = cursor.fetchone()
        self.assertIsNone(results)
