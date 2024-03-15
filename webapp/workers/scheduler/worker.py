import asyncio
from datetime import datetime, timedelta

from redis.asyncio import Redis

from webapp.core import redis_helper
from webapp.core.constants import Channel
from webapp.core.settings import init_test_settings, settings
from webapp.workers.redis_constants import AlarmActions, AlarmTaskInfo
from webapp.workers.redis_constants import RedisKeys as rk
from webapp.workers.scheduler.scheduler import Scheduler
from webapp.workers.scheduler.tasks import alarm_task, weekly_report_task
from webapp.workers.utils import GracefulKiller


def nearest_weekday(day=0) -> datetime:
    today = datetime.today()
    diff = timedelta(days=(day - today.weekday()) % 7)
    return today + diff


def create_start_date(time: str) -> datetime:
    start_time = datetime.strptime(time, "%H:%M").time()
    start_date = datetime.combine(datetime.today(), start_time)
    if datetime.now() > start_date:
        start_date = start_date + timedelta(days=1)

    return start_date


async def handle_alarm_task(info: AlarmTaskInfo, scheduler: Scheduler, redis: Redis):
    args_key = rk.alarm_users(info.channel, info.alarm)
    if info.action == AlarmActions.add:
        if not await redis.exists(args_key):
            job = await scheduler.add_job(
                alarm_task,
                [info.alarm],
                start_date=create_start_date(info.alarm),
                interval=timedelta(days=1),
            )
            await redis.hset(rk.alarms_jobs, info.alarm, job.id)

        await redis.sadd(args_key, info.channel_id)

    elif info.action == AlarmActions.delete:
        await redis.srem(args_key, info.channel_id)
        # delete job if no args left for alarm
        alarm_args = [rk.alarm_users(channel, info.alarm) for channel in Channel]
        if not await redis.exists(*alarm_args):
            job_id = await redis.hget(rk.alarms_jobs, info.alarm)
            scheduler.remove_job(job_id)
            await redis.hdel(rk.alarms_jobs, info.alarm)


async def main():
    scheduler = Scheduler(settings.redis)
    nearest_monday = nearest_weekday(0)
    nearest_monday = nearest_monday.replace(hour=23, minute=0, second=0)
    await scheduler.add_job(
        weekly_report_task, start_date=nearest_monday, interval=timedelta(days=7)
    )
    loop = asyncio.get_event_loop()
    loop.call_soon(scheduler.start())

    gk = GracefulKiller()
    while not gk.exit_now():
        with redis_helper.async_connection() as redis:
            task_key = await redis.blpop(rk.alarm_queue, 1)
            if not task_key:
                continue

            info = AlarmTaskInfo.from_str(task_key)
            if not info:
                # logging
                pass

            await handle_alarm_task(info, scheduler, redis)

    scheduler.shutdown()


def worker(test_config: bool = False):
    if test_config:
        init_test_settings()

    asyncio.run(main())