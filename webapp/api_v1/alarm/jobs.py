from redis.asyncio import Redis as AsyncRedis

from webapp.core.models import User
from webapp.core.redis import AlarmActions, AlarmTaskInfo, RedisKeys


async def enqueue_alarm_setting(redis: AsyncRedis, user: User, alarm: str | None) -> int:
    action = AlarmActions.add if alarm else AlarmActions.delete
    task_key = AlarmTaskInfo(action, user.channel, user.channel_id, alarm)
    return await redis.rpush(RedisKeys.alarms_queue, task_key.to_str())
