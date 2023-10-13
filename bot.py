import os
import aiosqlite

from telegram.ext import Application, ApplicationBuilder, PersistenceInput, PicklePersistence

from constants import PERSISTENCE_PATH
from handlers import all_handlers
from commands.menu_commands import DefaultMenuCommands


async def post_init(bot_data: dict, application: Application) -> None:
    conn = await aiosqlite.connect(bot_data['db_path'])
    bot_data['db_conn'] = conn
    application.bot_data.update(bot_data)
    await application.bot.set_my_commands(DefaultMenuCommands().menu)


def configure_app() -> Application:

    application = ApplicationBuilder() \
                    .token(os.environ.get('HPJ_TOKEN')) \
                    .persistence(
                        PicklePersistence(filepath=PERSISTENCE_PATH,
                                          store_data=PersistenceInput(bot_data=False))) \
                    .build()

    application.add_handlers(all_handlers)

    return application
