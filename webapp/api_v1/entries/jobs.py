from datetime import datetime, timedelta

from redis.asyncio import Redis as AsyncRedis

from webapp.core import settings
from webapp.core.models import User
from webapp.core.redis import RedisKeys, ReportTaskInfo, ReportTaskProducer


async def enqueue_report_order(
    redis: AsyncRedis, user: User, start_date: str | None, end_date: str | None
) -> int:
    if not end_date:
        end_date = datetime.today()

    if not start_date:
        start_date = end_date - timedelta(days=settings.entry_store_days)

    task_key = ReportTaskInfo(
        user.id,
        user.channel,
        user.channel_id,
        ReportTaskProducer.channel,
        start_date,
        end_date,
    )

    return await redis.rpush(RedisKeys.reports_queue, task_key.to_str())
