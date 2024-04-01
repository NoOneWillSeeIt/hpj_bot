import json
import logging
from datetime import datetime, time

import httpx

from common.constants import Channel
from common.survey.hpj_questions import prepare_answers_for_db
from common.utils import concat_url, gen_jwt_token
from tg_bot.constants import bot_settings

API_VERSION_ENDPOINT = "api/v1"


def get_remote_url(endpoint: str) -> str:
    return concat_url(bot_settings.remote_url, API_VERSION_ENDPOINT, endpoint)


async def send_request(
    method: str,
    endpoint: str,
    *,
    query_params: dict | None = None,
    json: dict | None = None,
) -> tuple[bool, httpx.Response]:
    async with httpx.AsyncClient() as client:
        client.headers.update({"x-bearer": gen_jwt_token({"issuer": "tgbot"})})
        url = get_remote_url(endpoint)
        response = await client.request(method, url, params=query_params, json=json)
        return response.status_code == 200, response


async def order_report(
    chat_id: int,
    start_date: datetime | None,
    end_date: datetime | None,
) -> bool:

    ok, response = await send_request(
        "get",
        endpoint="entries/report",
        query_params={
            "channel": Channel.telegram,
            "channel_id": chat_id,
            "start": start_date,
            "end": end_date,
        },
    )
    if not ok:
        logging.error(f"Report wasnt ordered. Server responded with: {response}")

    return ok


async def save_alarm(chat_id: int, time: time | None) -> bool:

    parsed_time = time.strftime("%H:%M") if time else None
    ok, response = await send_request(
        "post",
        endpoint="users/set-alarm",
        json={
            "user": {"channel": Channel.telegram, "channel_id": chat_id},
            "alarm": parsed_time,
        },
    )
    if not ok:
        logging.error(
            f"Alarm wasn't set to {parsed_time}. Server responded with: {response}"
        )

    return ok


async def is_new_user(chat_id: int) -> bool:

    ok, response = await send_request(
        "get",
        endpoint="users/is-new-user",
        query_params={
            "channel": Channel.telegram,
            "channel_id": chat_id,
        },
    )
    if not ok:
        logging.error(f"is-new-user endpoint answered with: {response}")
        return True

    resp_json = json.loads(response.text)
    return resp_json.get("is_new", True)


async def save_report(chat_id: int, replies: dict[str, str]) -> bool:

    date, report = prepare_answers_for_db(replies)
    ok, response = await send_request(
        "post",
        endpoint="entries/save-entry",
        json={
            "user": {"channel": Channel.telegram, "channel_id": chat_id},
            "date": date,
            "entry": report,
        },
    )
    if not ok:
        logging.error(f"Report wasn't saved. Server responded with: {response}")

    return ok


async def set_remote_webhooks(webhook_url: str):

    ok, response = await send_request(
        "post",
        endpoint="webhooks/subscribe",
        json={"channel": Channel.telegram, "url": webhook_url},
    )
    if not ok:
        raise ConnectionError(f"Can't set webhooks. Server responded with: {response}")


async def delete_remote_webhooks():

    ok, response = await send_request(
        "post",
        endpoint="webhooks/unsubscribe",
        json={"channel": Channel.telegram},
    )
    if not ok:
        raise ConnectionError(f"Can't set webhooks. Server responded with: {response}")
