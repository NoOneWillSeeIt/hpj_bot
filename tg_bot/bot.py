import asyncio

import uvicorn
from fastapi import FastAPI, Request, Response, UploadFile
from pydantic import BaseModel
from telegram import Update
from telegram.ext import (
    Application,
    ApplicationBuilder,
    PersistenceInput,
    PicklePersistence,
)

from tg_bot.commands import DefaultMenuCommands
from tg_bot.constants import PERSISTENCE_PATH, bot_settings
from tg_bot.handlers import ALL_COMMAND_HANDLERS, ERROR_HANDLER
from tg_bot.handlers.webhooks import WebhookAlarmsUpdate, WebhookReportUpdate


async def post_init(application: Application) -> None:
    """Post initialization handler. Updating bot data and setting commands for menu"""
    await application.bot.set_my_commands(DefaultMenuCommands().menu)


def configure_bot(test_config: bool = False) -> Application:
    """Configure and build app, add handlers"""
    token = bot_settings.test_token if test_config else bot_settings.token
    application = (
        ApplicationBuilder()
        .token(token)
        .persistence(
            PicklePersistence(
                filepath=PERSISTENCE_PATH, store_data=PersistenceInput(bot_data=False)
            )
        )
        .post_init(post_init)
        .build()
    )

    application.add_handlers(ALL_COMMAND_HANDLERS)
    application.add_error_handler(ERROR_HANDLER)

    return application


class WebhookAlarmsRequest(BaseModel):
    channel_ids: list[int]
    time: str


def configure_webapp(bot_app: Application) -> FastAPI:
    app = FastAPI()

    @app.post("/telegram")
    async def telegram_updates(req: Request) -> Response:
        await bot_app.update_queue.put(
            Update.de_json(data=await req.json(), bot=bot_app.bot)
        )
        return Response()

    @app.get("/healthcheck")
    async def healthcheck() -> str:
        return "bot is UP!"

    @app.post("/webhooks/alarms")
    async def alarms_webhook(body: WebhookAlarmsRequest):
        for chat_id in body.channel_ids:
            await bot_app.update_queue.put(
                WebhookAlarmsUpdate(chat_id=chat_id, time=body.time)
            )

    @app.post("/webhooks/reports/{channel_id}")
    async def reports_webhook(channel_id: int, file: UploadFile | None = None):
        if file:
            file_content, filename = await file.read(), file.filename
        else:
            file_content, filename = None, None

        await bot_app.update_queue.put(
            WebhookReportUpdate(
                chat_id=channel_id,
                report_file=file_content,
                filename=filename,
            )
        )

    return app


async def run_bot(bot_app: Application, server: uvicorn.Server, webhook_url: str):
    await bot_app.bot.set_webhook(url=webhook_url, allowed_updates=Update.ALL_TYPES)

    async with bot_app:
        await bot_app.start()
        await server.serve()
        await bot_app.stop()


def start_bot(host: str, port: int, remote_url: str, test_config: bool = False):
    bot_app = configure_bot(test_config)
    webapp = configure_webapp(bot_app)
    server = uvicorn.Server(uvicorn.Config(webapp, host=host, port=port))

    asyncio.run(run_bot(bot_app, server, f"{host}:{port}/telegram"))
