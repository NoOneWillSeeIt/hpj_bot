import asyncio
from datetime import datetime
import os
import re
from typing import Any
from unittest.mock import AsyncMock

from telegram import CallbackQuery, Chat, Message, MessageEntity, Update, User
from telegram.ext import Application, ApplicationBuilder, ExtBot, PersistenceInput, \
    PicklePersistence


TEST_TOKEN = os.environ.get('HPJ_TEST_TOKEN')
TEST_CHAT_ID = os.environ.get('HPJ_TEST_CHAT')
CMD_PATTERN = re.compile(r"/[\da-z_]{1,32}(?:@\w{1,32})?")


def make_app() -> Application:
    return ApplicationBuilder().token(TEST_TOKEN).persistence(
        PicklePersistence(filepath='test_persistence',
                          store_data=PersistenceInput(bot_data=False))).build()


def make_message(bot: ExtBot, text: str, entity: str) -> Message:
    entities = None
    if entity is MessageEntity.BOT_COMMAND:
        match = re.search(CMD_PATTERN, text)
        entities = [MessageEntity(MessageEntity.BOT_COMMAND, match.start(0), len(match.group(0)))]

    message = Message(
        message_id=-1,
        date=datetime.now(),
        chat=Chat(TEST_CHAT_ID, 'PRIVATE'),
        text=text,
        entities=entities,
        from_user=User(id=1, first_name="", is_bot=False),
    )
    message.set_bot(bot)
    message._unfreeze()
    return message


def make_callback_query(bot: ExtBot, data: str | None, msg: Message | None = None) -> CallbackQuery:
    callback = CallbackQuery(
        id=-2,
        from_user=User(1, "", False),
        chat_instance=Chat(TEST_CHAT_ID, 'PRIVATE'),
        message=msg,
        data=data
    )
    callback._unfreeze()
    callback.set_bot(bot)
    return callback


def make_update(bot: ExtBot, msg: Message | None, callback: CallbackQuery | None) -> Update:
    update = Update(
        update_id=-1,
        message=msg,
        callback_query=callback,
    )
    update._unfreeze()
    update.set_bot(bot)
    return update


def make_command(bot: ExtBot, text: str) -> Message:
    return make_message(bot, text, MessageEntity.BOT_COMMAND)


def make_text_message(bot: ExtBot, text: str) -> Message:
    return make_message(bot, text, None)


async def send_to_app(app: Application, msg: Message, callback: CallbackQuery) -> None:
    return await app.process_update(make_update(app.bot, msg, callback))


async def send_command(app: Application, text: str) -> None:
    return await send_to_app(app, make_command(app.bot, text), None)


async def send_message(app: Application, text: str) -> None:
    return await send_to_app(app, make_text_message(app.bot, text), None)


async def send_callback(app: Application, message: Message, data: str) -> None:
    return await send_to_app(app, message, make_callback_query(app.bot, data, message))


class AsyncResultCacheMock(AsyncMock):

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._result_cache = []

    async def __call__(self, *args: Any, **kwargs: Any) -> Any:
        call_result = super().__call__(*args, **kwargs)
        if asyncio.iscoroutine(call_result):
            result = await call_result
        else:
            result = call_result
        self._result_cache.append(result)
        return result

    @property
    def result_cache(self):
        return self._result_cache