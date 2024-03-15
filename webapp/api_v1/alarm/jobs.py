from redis.asyncio import Redis as AsyncRedis

from webapp.core.models import User
from webapp.workers.redis_constants import AlarmActions, AlarmTaskInfo, RedisKeys


async def _create_and_push_task(
    redis: AsyncRedis, action: AlarmActions, user: User, alarm: str
) -> int:
    task_key = AlarmTaskInfo(action, user.channel, user.channel_id, alarm)
    return await redis.rpush(RedisKeys.alarms_queue, task_key.to_str())


async def enqueue_alarm_deleting(redis: AsyncRedis, user: User) -> int:
    return await _create_and_push_task(redis, AlarmActions.delete, user, user.alarm)


async def enqueue_alarm_setting(redis: AsyncRedis, user: User, alarm: str) -> int:
    return await _create_and_push_task(redis, AlarmActions.delete, user, alarm)
