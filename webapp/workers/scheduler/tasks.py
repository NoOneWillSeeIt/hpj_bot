import asyncio
from datetime import datetime, timedelta

import redis.asyncio as aredis
from sqlalchemy.future import select

from webapp.core import db_helper, redis_helper
from webapp.core.constants import Channel
from webapp.core.models import User
from webapp.core.redis import RedisKeys as rk
from webapp.core.redis import ReportTaskInfo, ReportTaskProducer


async def call_channel_hook(url: str, payload: dict):
    # TODO: write async call. requests module is sync and will block worker
    ...


async def alarm_task(time: str):
    futures = []
    async with redis_helper.async_connection() as redis:
        for channel in Channel:
            channel_subs = await redis.smembers(rk.alarms_users(channel, time))
            if not channel_subs:
                continue

            channel_url = await redis.get(rk.webhooks_url(channel))
            coro = call_channel_hook(
                f"{channel_url}/channel-alarm",
                {"channel_ids": channel_subs, "time": time},
            )
            futures.append(coro)

    asyncio.gather(*futures)


async def get_channel_users(channels: list[Channel]) -> list[User]:
    users = []
    async with db_helper.async_session() as session:
        stmt = select(User).where(User.channel.in_(channels))
        result = await session.execute(stmt)
        users = result.scalars().all()

    return users


async def order_report(
    redis_client: aredis.Redis,
    user: User,
    producer: ReportTaskProducer,
    interval: list[str],
):
    task = ReportTaskInfo(
        user.id, user.channel, user.channel_id, producer, interval[0], interval[-1]
    )
    await redis_client.rpush(rk.reports_queue, task.to_str())


async def weekly_report_task():
    coros = []
    async with redis_helper.async_connection() as redis:
        today = datetime.today()
        weekday = today.isoweekday()
        last_week_interval = (
            (today - timedelta(days=weekday + 6)).strftime("%d.%m.%y"),  # monday
            (today - timedelta(days=weekday)).strftime("%d.%m.%y"),  # sunday
        )

        ch_list = list(Channel)
        ch_urls = await redis.mget([rk.webhooks_url(ch) for ch in ch_list])
        available_channels = [
            ch for ch, url in zip(ch_list, ch_urls) if url is not None
        ]

        users = get_channel_users(available_channels)

        coros = [
            order_report(redis, user, ReportTaskProducer.scheduler, last_week_interval)
            for user in users
        ]

        asyncio.gather(*coros)
