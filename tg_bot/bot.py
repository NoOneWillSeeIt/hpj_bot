from typing import Dict
import aiosqlite

from telegram.ext import Application, ApplicationBuilder, PersistenceInput, PicklePersistence

from tg_bot.constants import DB_PATH, HPJ_BOT_TOKEN, JINJA_TEMPLATE_PATH, JOURNAL_TEMPLATE, \
    PERSISTENCE_PATH, OutputFileFormats
from tg_bot.handlers import ALL_COMMAND_HANDLERS, ERROR_HANDLER
from tg_bot.commands import DefaultMenuCommands
from tg_bot.journal_view import HTMLGenerator, IFileGenerator


def filegens() -> Dict[str, Dict[str, IFileGenerator]]:
    return {
        'file_generators': {
            OutputFileFormats.HTML: HTMLGenerator(JINJA_TEMPLATE_PATH, JOURNAL_TEMPLATE),
        },
    }


async def post_init(application: Application) -> None:
    """Post initialization handler. Updating bot data and setting commands for menu"""
    conn = await aiosqlite.connect(DB_PATH)
    db_data = {
        'db_conn': conn,
        'db_path': DB_PATH,
    }
    application.bot_data.update({
        **db_data,
        **filegens(),
    })
    await application.bot.set_my_commands(DefaultMenuCommands().menu)


def configure_app() -> Application:
    """Configure and build app, add handlers"""
    application = ApplicationBuilder() \
        .token(HPJ_BOT_TOKEN) \
        .persistence(
            PicklePersistence(filepath=PERSISTENCE_PATH,
                              store_data=PersistenceInput(bot_data=False))) \
        .post_init(post_init) \
        .build()

    application.add_handlers(ALL_COMMAND_HANDLERS)
    application.add_error_handler(ERROR_HANDLER)

    return application
