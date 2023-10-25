import json
import unittest
from unittest.mock import AsyncMock

from telegram import Update
from bot import filegens
from commands.commands import HPJCommands

from handlers import LOAD_CALLBACK_HANDLER, LOAD_HANDLER
from hpj_questions import Questions, prepare_answers_for_db
from tests.utils.common import create_test_db
from tests.utils.ptb_app import TEST_CHAT_ID, AsyncResultCacheMock, make_app, make_text_message, \
    send_callback, send_command


class LoadJournalHandlersTest(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self) -> None:
        self.app = make_app()
        self.app.add_handlers([LOAD_HANDLER, LOAD_CALLBACK_HANDLER])
        db_path, conn = await create_test_db()
        self.app.bot_data['db_path'] = db_path
        self.app.bot_data['db_conn'] = conn
        self.app.bot_data.update(filegens())
        self.conn = conn

        await self.app.initialize()
        self.app.bot._unfreeze()
        return await super().asyncSetUp()

    async def asyncTearDown(self) -> None:
        self.app.shutdown()
        return await super().asyncTearDown()

    async def test_load_callback_wrong_data(self):
        self.assertIsNone(
            LOAD_CALLBACK_HANDLER.check_update(Update(-1, make_text_message(self.app.bot, 'xmlns')))
        )

    async def test_load_callback_no_entries(self):
        answer_mock = AsyncMock(return_value=None)
        self.app.bot.answer_callback_query = answer_mock

        send_amock = AsyncResultCacheMock(wraps=self.app.bot.send_message)
        self.app.bot.send_message = send_amock

        edit_amock = AsyncMock(wraps=self.app.bot.edit_message_text)
        self.app.bot.edit_message_text = edit_amock

        await send_command(self.app, f'/{HPJCommands.LOAD}')
        await send_callback(self.app, send_amock.result_cache[-1], 'html')

        answer_mock.assert_awaited()
        self.assertEqual(
            'У меня нет твоих записей ¯\\_(ツ)_/¯'.lower(),
            edit_amock.await_args.kwargs['text'].lower()
        )

    async def test_load_callback_has_entries(self):
        answer_mock = AsyncMock(return_value=None)
        self.app.bot.answer_callback_query = answer_mock

        send_amock = AsyncResultCacheMock(wraps=self.app.bot.send_message)
        self.app.bot.send_message = send_amock

        edit_amock = AsyncMock(wraps=self.app.bot.edit_message_text)
        self.app.bot.edit_message_text = edit_amock

        send_doc_amock = AsyncMock(wraps=self.app.bot.send_document)
        self.app.bot.send_document = send_doc_amock

        entry = {}
        key, entry = prepare_answers_for_db({
            Questions.Date: '23.04',
            Questions.HadPain: 'Нет',
            Questions.Painkillers: 'Нет',
            Questions.Comments: 'Нет комментариев',
        })
        await self.conn.execute(
            '''
            INSERT INTO journal(chat_id, entries)
            VALUES
            (
                :chat_id,
                json_object(
                    :key,
                    json(:entry)
                )
            )
            ''',
            {'chat_id': TEST_CHAT_ID,
             'key': key,
             'entry': json.dumps(entry, ensure_ascii=False)}
        )
        await self.conn.commit()

        await send_command(self.app, f'/{HPJCommands.LOAD}')
        await send_callback(self.app, send_amock.result_cache[-1], 'html')

        answer_mock.assert_awaited()
        self.assertEqual(
            'Вот те записи, что у меня есть:'.lower(),
            edit_amock.await_args.kwargs['text'].lower()
        )
        send_doc_amock.assert_awaited()
