from typing import Annotated

from fastapi import File
from pydantic import BaseModel
from telegram.ext import Application, CallbackContext, ExtBot, TypeHandler

from tg_bot.commands.commands import HPJCommands
from tg_bot.constants import FLASK_PIC_PATH


class WebhookAlarmsUpdate(BaseModel):
    chat_id: int
    time: str


class WebhookReportUpdate(BaseModel):
    chat_id: int
    report_file: Annotated[bytes, File()] | None
    filename: str | None


class CustomContext(CallbackContext[ExtBot, dict, dict, dict]):

    @classmethod
    def from_update(
        cls,
        update: object,
        application: Application,
    ) -> "CustomContext":
        if isinstance(update, WebhookAlarmsUpdate):
            return cls(application=application)
        if isinstance(update, WebhookReportUpdate):
            return cls(application=application, chat_id=update.chat_id)
        return super().from_update(update, application)


async def alarms_update(update: WebhookAlarmsUpdate, context: CustomContext):
    reminder_text = (
        f"Привет, время заполнить журнал. Напиши /{HPJCommands.ADD_ENTRY} и вперёд!"
    )
    if not (context.chat_data and context.chat_data.get("survey")):
        await context.bot.send_message(update.chat_id, reminder_text)


async def report_update(update: WebhookReportUpdate, context: CustomContext):
    queries = context.chat_data.get("report_queries")
    if queries:
        query_inline_message_id = queries.pop(0)
        text = (
            "Вот те записи, что у меня есть:"
            if update.report_file
            else "У меня нет твоих записей ¯\\_(ツ)_/¯"
        )
        await context.bot.edit_message_text(
            text=text, inline_message_id=query_inline_message_id, reply_markup=None
        )

    if update.report_file:
        await context.bot.send_document(
            chat_id=update.chat_id,
            document=update.report_file,
            filename=update.filename,
            thumbnail=FLASK_PIC_PATH,
        )


ALARM_HOOK_HANDLER = TypeHandler(
    type=WebhookAlarmsUpdate,
    callback=alarms_update,
)
REPORT_HOOK_HANDLER = TypeHandler(
    type=WebhookReportUpdate,
    callback=report_update,
)
