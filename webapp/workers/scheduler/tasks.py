import asyncio
import logging
from datetime import datetime, timedelta
from typing import Sequence

import httpx
import redis.asyncio as aredis
from sqlalchemy import delete, select

from common.constants import (
    CERTS_DIR,
    DAYS_TO_STORE_ENTRIES,
    ENTRY_DATE_FORMAT,
    Channel,
)
from common.utils import concat_url, gen_jwt_token
from webapp.core import db_helper, redis_helper
from webapp.core.models import JournalEntry, User
from webapp.core.redis import RedisKeys as rk
from webapp.core.redis import ReportRequester, ReportTaskInfo


async def call_channel_hook(
    url: str,
    *,
    json: dict | None = None,
) -> httpx.Response:
    async with httpx.AsyncClient(verify=str(CERTS_DIR / "ssl-cert.pem")) as client:
        client.headers.update(
            {
                "Authorization": "Bearer "
                + gen_jwt_token({"issuer": "webapp", "reason": "alarms"})
            }
        )
        return await client.post(url, json=json)


async def alarm_task(time: str):
    futures = []
    async with redis_helper.async_connection() as redis:
        for channel in Channel:
            channel_subs = await redis.smembers(rk.alarms_users(channel, time))
            if not channel_subs:
                continue

            channel_url = await redis.get(rk.webhooks_url(channel))
            if not channel_url:
                logging.warning(
                    "No registered url for channel {channel}, but alarms was set"
                )
                continue

            coro = call_channel_hook(
                concat_url(str(channel_url), "alarms"),
                json={"channel_ids": list(channel_subs), "time": time},
            )
            futures.append(coro)

    await asyncio.gather(*futures)


async def get_channel_users(channels: list[Channel]) -> list[User]:
    users = []
    async with db_helper.async_session() as session:
        stmt = select(User).where(User.channel.in_(channels))
        result = await session.execute(stmt)
        users = list(result.scalars().all())

    return users


async def order_report(
    redis_client: aredis.Redis,
    user: User,
    requester: ReportRequester,
    interval: Sequence[str],
):
    task = ReportTaskInfo(
        user.id,
        Channel(user.channel),
        user.channel_id,
        requester,
        interval[0],
        interval[-1],
    )
    await redis_client.rpush(rk.reports_queue, task.to_str())


async def weekly_report_task():
    coros = []
    async with redis_helper.async_connection() as redis:
        today = datetime.today()
        weekday = today.isoweekday()
        last_week_interval = (
            (today - timedelta(days=weekday + 6)).strftime(ENTRY_DATE_FORMAT),  # monday
            (today - timedelta(days=weekday)).strftime(ENTRY_DATE_FORMAT),  # sunday
        )

        ch_list = list(Channel)
        ch_urls = await redis.mget([rk.webhooks_url(ch) for ch in ch_list])
        available_channels = [
            ch for ch, url in zip(ch_list, ch_urls) if url is not None
        ]

        users = await get_channel_users(available_channels)

        coros = [
            order_report(redis, user, ReportRequester.webapp, last_week_interval)
            for user in users
        ]

        await asyncio.gather(*coros)


async def db_cleaner_task():
    today = datetime.today()
    allowed_dates = [
        (today - timedelta(days=i)).strftime(ENTRY_DATE_FORMAT)
        for i in range(DAYS_TO_STORE_ENTRIES)
    ]
    async with db_helper.async_session() as session:
        stmt = select(JournalEntry.id).filter(JournalEntry.date.not_in(allowed_dates))
        entries = await session.execute(stmt)
        entries = list(entries.scalars().all())
        if entries:
            del_stmt = delete(JournalEntry).where(JournalEntry.id.in_(entries))
            await session.execute(del_stmt)
            await session.commit()
        logging.info(f"Deleted {len(entries)} rows from JournalEntry")
