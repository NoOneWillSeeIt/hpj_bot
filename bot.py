import os
import aiosqlite

from telegram.ext import Application, ApplicationBuilder, PersistenceInput, PicklePersistence

from constants import DB_PATH, JINJA_TEMPLATE_PATH, JOURNAL_TEMPLATE, PERSISTENCE_PATH, \
    OutputFileFormats
from handlers import all_handlers, error_handler
from commands import DefaultMenuCommands
from journal_view.html_generator import HTMLGenerator


async def post_init(application: Application) -> None:
    conn = await aiosqlite.connect(DB_PATH)
    bot_data = {
        'db_conn': conn,
        'db_path': DB_PATH,
        'file_generators': {
            OutputFileFormats.HTML: HTMLGenerator(JINJA_TEMPLATE_PATH, JOURNAL_TEMPLATE),
        },
    }
    application.bot_data.update(bot_data)
    await application.bot.set_my_commands(DefaultMenuCommands().menu)


def configure_app() -> Application:

    application = ApplicationBuilder() \
                    .token(os.environ.get('HPJ_TOKEN')) \
                    .persistence(
                        PicklePersistence(filepath=PERSISTENCE_PATH,
                                          store_data=PersistenceInput(bot_data=False))) \
                    .post_init(post_init) \
                    .build()

    application.add_handlers(all_handlers)
    application.add_error_handler(error_handler)

    return application
