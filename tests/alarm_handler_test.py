from datetime import datetime
import unittest

from telegram import Update

from commands.commands import HPJCommands
from constants import MSK_TIMEZONE_OFFSET, TIME_FORMAT

from handlers import ALARM_CONVO_HANDLER, ALARM_CANCEL_HANDLER
from tests.utils.common import create_test_db
from tests.utils.ptb_app import TEST_CHAT_ID, make_app, make_command, send_command, send_message


class AlarmHandlersTest(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self) -> None:
        self.app = make_app()
        self.app.add_handlers([ALARM_CONVO_HANDLER, ALARM_CANCEL_HANDLER])
        db_path, conn = await create_test_db()
        self.app.bot_data['db_path'] = db_path
        self.app.bot_data['db_conn'] = conn
        self.conn = conn

        await self.app.initialize()
        return await super().asyncSetUp()

    async def asyncTearDown(self) -> None:
        self.app.shutdown()
        return await super().asyncTearDown()

    async def _check_convo_ready_to_start(self):
        new_update = Update(-1, make_command(self.app.bot, f'/{HPJCommands.ALARM}'))
        return ALARM_CONVO_HANDLER.check_update(new_update)

    async def test_alarm(self):
        test_time = '23:15'
        await send_command(self.app, f'/{HPJCommands.ALARM} {test_time}')

        cur = await self.conn.execute('select alarm from journal where chat_id = :chat_id',
                                      {'chat_id': TEST_CHAT_ID})
        res = await cur.fetchone()

        check_time = datetime.strptime(test_time, '%H:%M').time()
        check_time = check_time.replace(tzinfo=MSK_TIMEZONE_OFFSET)
        self.assertEqual(res[0], check_time.strftime(TIME_FORMAT))
        self.assertIsNotNone(self._check_convo_ready_to_start())

    async def test_alarm_wrong_time(self):
        test_time = '29:30'
        await send_command(self.app, f'/{HPJCommands.ALARM} {test_time}')

        await send_message(self.app, f'{test_time}')

        cur = await self.conn.execute('select alarm from journal where chat_id = :chat_id',
                                      {'chat_id': TEST_CHAT_ID})
        res = await cur.fetchone()

        self.assertIsNone(res)
        self.assertIsNotNone(self._check_convo_ready_to_start())

    async def test_cancel_alarm(self):
        await send_command(self.app, f'/{HPJCommands.ALARM} 23:15')

        for msg in ['first alarm cancel', 'second alarm cancel']:
            await send_command(self.app, f'/{HPJCommands.CANCEL}')

            cur = await self.conn.execute('select alarm from journal where chat_id = :chat_id',
                                          {'chat_id': TEST_CHAT_ID})
            res = await cur.fetchone()
            self.assertIsNone(res[0], msg)

    async def test_alarm_convo(self):
        await send_command(self.app, f'/{HPJCommands.ALARM}')

        test_time = '23:15'
        await send_message(self.app, f'{test_time}')

        cur = await self.conn.execute('select alarm from journal where chat_id = :chat_id',
                                      {'chat_id': TEST_CHAT_ID})
        res = await cur.fetchone()

        check_time = datetime.strptime(test_time, '%H:%M').time()
        check_time = check_time.replace(tzinfo=MSK_TIMEZONE_OFFSET)
        self.assertEqual(res[0], check_time.strftime(TIME_FORMAT))
        self.assertIsNotNone(self._check_convo_ready_to_start())

    async def test_alarm_convo_wrong_time(self):
        await send_command(self.app, f'/{HPJCommands.ALARM}')

        test_time = '29:30'
        await send_message(self.app, f'{test_time}')

        cur = await self.conn.execute('select alarm from journal where chat_id = :chat_id',
                                      {'chat_id': TEST_CHAT_ID})
        res = await cur.fetchone()
        self.assertIsNone(res)
        self.assertIsNotNone(self._check_convo_ready_to_start())
