import httpx
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackQueryHandler, CommandHandler, ContextTypes

from common.constants import OutputFileFormats
from tg_bot.commands import HPJCommands
from tg_bot.requests import order_report


class LoadJournalHandlers:
    """Handlers for loading full journal."""

    @classmethod
    async def load(cls, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handles /load command and suggests file formats."""
        keyboard = [
            [
                InlineKeyboardButton(file_format.name, callback_data=file_format.value)
                for file_format in OutputFileFormats
            ]
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text("Выбери формат:", reply_markup=reply_markup)

    @classmethod
    async def load_choose(cls, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handles file format choosing. Generates report and send it to user."""
        query = update.callback_query
        await query.answer()
        err = await order_report(query.message.chat_id)
        if err:
            if (
                isinstance(err, httpx.HTTPStatusError)
                and err.response.status_code == httpx.codes.NOT_FOUND
            ):
                await query.edit_message_text("У меня нет твоих записей")
                return

            await context.application.process_error(update, err)
            await query.edit_message_text(
                "Не удалось запросить отчёт. Попробуй позже.", reply_markup=None
            )
            return

        context.chat_data.setdefault("report_queries", []).append(
            query.message.message_id
        )


LOAD_HANDLER = CommandHandler(HPJCommands.LOAD, LoadJournalHandlers.load)


LOAD_CALLBACK_HANDLER = CallbackQueryHandler(
    LoadJournalHandlers.load_choose,
    pattern="^" + "|".join(ext.value for ext in OutputFileFormats) + "$",
)
