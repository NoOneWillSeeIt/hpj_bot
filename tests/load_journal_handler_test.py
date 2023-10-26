from collections import namedtuple
import json
from unittest.mock import AsyncMock

from telegram import Update
from bot import filegens
from commands.commands import HPJCommands

from handlers import LOAD_CALLBACK_HANDLER, LOAD_HANDLER
from hpj_questions import Questions, prepare_answers_for_db
from tests.utils.ptb_app import TEST_CHAT_ID, make_text_message, send_callback, send_command
from tests.utils.test_cases import AsyncResultCacheMock, AsyncTelegramBotTestCase


BotMocks = namedtuple(
    'BotMocks', ['answer', 'send', 'edit', 'send_doc']
)


class LoadJournalHandlersTest(AsyncTelegramBotTestCase):

    _handlers = [LOAD_HANDLER, LOAD_CALLBACK_HANDLER]

    async def asyncSetUp(self) -> None:
        await super().asyncSetUp()
        self.app.bot_data.update(filegens())

    async def test_load_callback_wrong_data(self):
        self.assertIsNone(
            LOAD_CALLBACK_HANDLER.check_update(Update(-1, make_text_message(self.app.bot, 'xmlns')))
        )

    def _create_bot_method_mocks(self) -> BotMocks:
        answer = AsyncMock(return_value=None)
        self.app.bot.answer_callback_query = answer

        send = AsyncResultCacheMock(wraps=self.app.bot.send_message)
        self.app.bot.send_message = send

        edit = AsyncMock(wraps=self.app.bot.edit_message_text)
        self.app.bot.edit_message_text = edit

        send_doc = AsyncMock(wraps=self.app.bot.send_document)
        self.app.bot.send_document = send_doc

        return BotMocks(answer, send, edit, send_doc)

    async def test_load_callback_no_entries(self):
        mocks = self._create_bot_method_mocks()

        await send_command(self.app, f'/{HPJCommands.LOAD}')
        await send_callback(self.app, mocks.send.result_cache[-1], 'html')

        mocks.answer.assert_awaited()
        self.assertEqual(
            'У меня нет твоих записей ¯\\_(ツ)_/¯'.lower(),
            mocks.edit.await_args.kwargs['text'].lower()
        )

    async def test_load_callback_has_entries(self):
        mocks = self._create_bot_method_mocks()

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
        await send_callback(self.app, mocks.send.result_cache[-1], 'html')

        mocks.answer.assert_awaited()
        self.assertEqual(
            'Вот те записи, что у меня есть:'.lower(),
            mocks.edit.await_args.kwargs['text'].lower()
        )
        mocks.send_doc.assert_awaited()
