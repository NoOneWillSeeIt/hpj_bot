from datetime import datetime
import os
import re

from telegram import Chat, Message, MessageEntity, Update, User
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
    return message


def make_command(bot: ExtBot, text: str) -> Message:
    return make_message(bot, text, MessageEntity.BOT_COMMAND)


def make_text_message(bot: ExtBot, text: str) -> Message:
    return make_message(bot, text, None)


async def send_to_app(app: Application, msg: Message) -> None:
    return await app.process_update(Update(-1, msg))


async def send_command(app: Application, text: str) -> None:
    return await send_to_app(app, make_command(app.bot, text))


async def send_message(app: Application, text: str) -> None:
    return await send_to_app(app, make_text_message(app, text))
