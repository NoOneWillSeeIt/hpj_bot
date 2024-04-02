import json
import logging
from datetime import datetime, time
from typing import TypeAlias

import httpx

from common.constants import Channel
from common.survey.hpj_questions import prepare_answers_for_db
from common.utils import concat_url, gen_jwt_token
from tg_bot.constants import bot_settings

HttpxErrors: TypeAlias = (
    httpx.HTTPError | httpx.InvalidURL | httpx.StreamError | httpx.CookieConflict
)

OptionalHttpxErr: TypeAlias = HttpxErrors | None


def get_remote_url(endpoint: str) -> str:
    return concat_url(
        bot_settings.remote.url, bot_settings.remote.api_endpoint, endpoint
    )


async def send_request(
    method: str,
    endpoint: str,
    *,
    query_params: dict | None = None,
    json: dict | None = None,
) -> tuple[OptionalHttpxErr, httpx.Response | None]:
    try:
        async with httpx.AsyncClient() as client:
            client.headers.update(
                {"Authorization": "Bearer " + gen_jwt_token({"issuer": "tgbot"})}
            )
            url = get_remote_url(endpoint)
            response = await client.request(method, url, params=query_params, json=json)
            response.raise_for_status()
            return None, response

    except (
        httpx.HTTPError,
        httpx.InvalidURL,
        httpx.StreamError,
        httpx.CookieConflict,
    ) as ex:
        logging.error(ex)
        return ex, None


async def order_report(
    chat_id: int,
    start_date: datetime | None,
    end_date: datetime | None,
) -> OptionalHttpxErr:

    err, _ = await send_request(
        "get",
        endpoint="entries/report",
        query_params={
            "channel": Channel.telegram,
            "channel_id": chat_id,
            "start": start_date,
            "end": end_date,
        },
    )
    if err:
        logging.error(f"Report wasnt ordered. Error: {err}")

    return err


async def save_alarm(chat_id: int, time: time | None) -> OptionalHttpxErr:

    parsed_time = time.strftime("%H:%M") if time else None
    err, _ = await send_request(
        "post",
        endpoint="users/set-alarm",
        json={
            "user": {"channel": Channel.telegram, "channel_id": chat_id},
            "alarm": parsed_time,
        },
    )
    if err:
        logging.error(f"Alarm wasn't set due to network error: {err}")

    return err


async def is_new_user(chat_id: int) -> bool:

    err, response = await send_request(
        "get",
        endpoint="users/is-new-user",
        query_params={
            "channel": Channel.telegram,
            "channel_id": chat_id,
        },
    )
    if err:
        logging.error(f"New user check returned with error: {err}")
        return True

    resp_json = json.loads(response.text if response else "")
    return resp_json.get("is_new", True)


async def save_report(chat_id: int, replies: dict[str, str]) -> OptionalHttpxErr:

    date, report = prepare_answers_for_db(replies)
    err, _ = await send_request(
        "post",
        endpoint="entries/save-entry",
        json={
            "user": {"channel": Channel.telegram, "channel_id": chat_id},
            "date": date,
            "entry": report,
        },
    )
    if err:
        logging.error(f"Report wasn't saved. Error: {err}")

    return err


async def set_remote_webhooks(webhook_url: str):

    err, _ = await send_request(
        "post",
        endpoint="webhooks/subscribe",
        json={"channel": Channel.telegram, "url": webhook_url},
    )
    if err:
        raise ConnectionError(f"Can't set webhooks. Caught error: {err}")


async def delete_remote_webhooks():

    err, _ = await send_request(
        "post",
        endpoint="webhooks/unsubscribe",
        json={"channel": Channel.telegram},
    )
    if err:
        raise ConnectionError(f"Can't set webhooks. Caught error: {err}")
