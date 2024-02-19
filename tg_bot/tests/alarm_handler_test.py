from datetime import datetime

from telegram import Update

from tg_bot.commands.commands import HPJCommands
from tg_bot.constants import MSK_TIMEZONE_OFFSET, TIME_FORMAT
from tg_bot.handlers import ALARM_CONVO_HANDLER, ALARM_CANCEL_HANDLER
from tg_bot.tests.utils.ptb_app import TEST_CHAT_ID, make_command, send_command, send_message
from tg_bot.tests.utils.test_cases import AsyncTelegramBotTestCase


class AlarmHandlersTest(AsyncTelegramBotTestCase):
    """Alarm convo handlers test cases"""

    _handlers = [ALARM_CONVO_HANDLER, ALARM_CANCEL_HANDLER]

    def _check_convo_ready_to_start(self):
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
