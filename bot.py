import os

from telegram.ext import Application, ApplicationBuilder

from handlers import all_handlers
from menu_commands import DefaultMenuCommands


async def post_init(application: Application) -> None:
    await application.bot.set_my_commands(DefaultMenuCommands().menu)


def configure_app() -> Application:

    application = ApplicationBuilder().token(os.environ.get('HPJ_TOKEN')).\
        post_init(post_init).build()
    
    application.add_handlers(all_handlers)

    return application
