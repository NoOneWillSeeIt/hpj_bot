from datetime import datetime

from redis.asyncio import Redis as AsyncRedis

from webapp.core.models import User
from webapp.workers.redis_constants import RedisKeys, ReportTaskInfo, ReportTaskProducer


async def enqueue_report_order(
    redis: AsyncRedis, user: User, start_date: str, end_date: str | None
) -> int:
    if not end_date:
        end_date = datetime.today()

    task_key = ReportTaskInfo(
        user.id,
        user.channel,
        user.channel_id,
        ReportTaskProducer.channel,
        start_date,
        end_date,
    )

    return await redis.rpush(RedisKeys.reports_queue, task_key)
