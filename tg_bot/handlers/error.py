import html
import json
import logging
import traceback

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from tg_bot.constants import bot_settings


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Reports error to dev chat."""
    logging.error("Update error: ", exc_info=context.error)

    tb_list = traceback.format_exception(context.error, limit=-20)
    tb_string = "".join(tb_list)

    update_str = update.to_dict() if isinstance(update, Update) else str(update)
    message = (
        "Bot caught an exception\n"
        f"<pre>update = {html.escape(json.dumps(update_str, indent=2, ensure_ascii=False))}"
        "</pre>\n\n"
        f"<pre>context.chat_data = {html.escape(str(context.chat_data))}</pre>\n\n"
        f"<pre>context.user_data = {html.escape(str(context.user_data))}</pre>\n\n"
    )
    trace_message = f"<pre>{html.escape(tb_string)}</pre>"

    await context.bot.send_message(
        chat_id=bot_settings.developer_chat_id, text=message, parse_mode=ParseMode.HTML
    )
    await context.bot.send_message(
        chat_id=bot_settings.developer_chat_id,
        text=trace_message,
        parse_mode=ParseMode.HTML,
    )
