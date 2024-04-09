import asyncio
from typing import Annotated

import httpx
import uvicorn
from fastapi import Depends, FastAPI, Form, Request, Response, UploadFile
from pydantic import BaseModel
from telegram import Update
from telegram.ext import (
    Application,
    ApplicationBuilder,
    ContextTypes,
    PersistenceInput,
    PicklePersistence,
)

from common.utils import check_jwt_token_dep, concat_url
from tg_bot.commands import DefaultMenuCommands
from tg_bot.constants import PERSISTENCE_PATH, bot_settings
from tg_bot.handlers import ALL_COMMAND_HANDLERS, ERROR_HANDLER
from tg_bot.handlers.webhooks import (
    CustomContext,
    WebhookAlarmsUpdate,
    WebhookReportUpdate,
)
from tg_bot.requests import delete_remote_webhooks, set_remote_webhooks


async def post_init(application: Application) -> None:
    """Post initialization handler. Updating bot data and setting commands for menu"""
    await application.bot.set_my_commands(DefaultMenuCommands().menu)


def configure_bot(test_config: bool = False) -> Application:
    """Configure and build app, add handlers"""
    token = bot_settings.test_token if test_config else bot_settings.token
    context_types = ContextTypes(CustomContext)
    application = (
        ApplicationBuilder()
        .token(token)
        .persistence(
            PicklePersistence(
                filepath=PERSISTENCE_PATH, store_data=PersistenceInput(bot_data=False)
            )
        )
        .context_types(context_types)
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

    @app.post("/webhooks/alarms", dependencies=[Depends(check_jwt_token_dep)])
    async def alarms_webhook(body: WebhookAlarmsRequest):
        for chat_id in body.channel_ids:
            await bot_app.update_queue.put(
                WebhookAlarmsUpdate(chat_id=chat_id, time=body.time)
            )

    @app.post("/webhooks/reports", dependencies=[Depends(check_jwt_token_dep)])
    async def reports_webhook(
        channel_id: Annotated[int, Form()], file: UploadFile | None = None
    ):
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
    await set_remote_webhooks(concat_url(webhook_url, "webhooks"))

    async with bot_app:
        await bot_app.post_init(bot_app)
        await bot_app.start()
        await bot_app.bot.set_webhook(
            url=concat_url(webhook_url, "telegram"),
            allowed_updates=Update.ALL_TYPES,
            certificate=bot_settings.ssl.certfile,
        )
        await server.serve()
        await delete_remote_webhooks()
        await bot_app.stop()
        await bot_app.bot.delete_webhook()


def start_bot(host: str, port: int, remote_url: str, test_config: bool = False):
    if remote_url:
        bot_settings.remote.url = remote_url

    bot_app = configure_bot(test_config)
    webapp = configure_webapp(bot_app)
    server = uvicorn.Server(
        uvicorn.Config(
            webapp,
            host=host,
            port=port,
            ssl_certfile=bot_settings.ssl.certfile,
            ssl_keyfile=bot_settings.ssl.key,
        )
    )

    url = httpx.URL(scheme="https", host=host, port=port)
    asyncio.run(run_bot(bot_app, server, str(url)))
