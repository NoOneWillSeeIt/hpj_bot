from redis.asyncio import Redis as AsyncRedis

from common.constants import Channel
from webapp.core.models import User
from webapp.core.redis import AlarmActions, AlarmTaskInfo, RedisKeys


async def enqueue_alarm_job(redis: AsyncRedis, action: AlarmActions, user: User, alarm: str) -> int:
    task_key = AlarmTaskInfo(action, Channel(user.channel), user.channel_id, alarm)
    return await redis.rpush(RedisKeys.alarms_queue, task_key.to_str())


async def enqueue_alarm_deleting(redis: AsyncRedis, user: User) -> int:
    if user.alarm is None:
        return 0
    return await enqueue_alarm_job(redis, AlarmActions.delete, user, user.alarm)


async def enqueue_alarm_setting(redis: AsyncRedis, user: User, alarm: str) -> int:
    return await enqueue_alarm_job(redis, AlarmActions.add, user, alarm)
