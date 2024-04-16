from datetime import datetime, timedelta

from redis.asyncio import Redis as AsyncRedis

from common.constants import ENTRY_DATE_FORMAT, Channel
from webapp.core import settings
from webapp.core.models import User
from webapp.core.redis import RedisKeys, ReportTaskInfo, ReportRequester


async def enqueue_report_order(
    redis: AsyncRedis, user: User, start_date: str | None, end_date: str | None
) -> int:
    if not end_date:
        end_date = datetime.today().strftime(ENTRY_DATE_FORMAT)

    if not start_date:
        end_dt = datetime.strptime(end_date, ENTRY_DATE_FORMAT)
        start_dt = end_dt - timedelta(days=settings.entry_store_days)
        start_date = start_dt.strftime(ENTRY_DATE_FORMAT)

    task_key = ReportTaskInfo(
        user.id,
        Channel(user.channel),
        user.channel_id,
        ReportRequester.channel,
        start_date,
        end_date,
    )

    return await redis.rpush(RedisKeys.reports_queue, task_key.to_str())
