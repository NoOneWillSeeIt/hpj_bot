import asyncio
import logging
import platform
from datetime import datetime, time, timedelta
from typing import Iterable

from redis.asyncio import Redis
from sqlalchemy import select

from common.constants import MSK_TIMEZONE_OFFSET, TIME_FMT, Channel
from webapp.core import db_helper, redis_helper
from webapp.core.models import User
from webapp.core.redis import AlarmActions, AlarmTaskInfo
from webapp.core.redis import RedisKeys as rk
from webapp.core.settings import init_test_settings, settings
from webapp.workers.scheduler.scheduler import Scheduler
from webapp.workers.scheduler.tasks import (
    alarm_task,
    db_cleaner_task,
    weekly_report_task,
)
from webapp.workers.utils import GracefulExit, GracefulKiller


def nearest_weekday(day=0) -> datetime:
    today = datetime.today()
    diff = timedelta(days=(day - today.weekday()) % 7)
    return today + diff


def create_start_date(time: str) -> datetime:
    start_time = datetime.strptime(time, TIME_FMT).time()
    start_date = datetime.combine(datetime.today(), start_time)

    return start_date


async def handle_alarm_task(info: AlarmTaskInfo, scheduler: Scheduler, redis: Redis):
    args_key = rk.alarms_users(info.channel, info.alarm)
    alarm_args = [rk.alarms_users(channel, info.alarm) for channel in Channel]

    if info.action == AlarmActions.add:
        # create new job it there was none planned for specific time
        if not await redis.exists(*alarm_args):
            job = await scheduler.add_job(
                alarm_task,
                [info.alarm],
                start_date=create_start_date(info.alarm),
                interval=timedelta(days=1),
            )
            await redis.hset(rk.alarms_job, info.alarm, job.id)

        await redis.sadd(args_key, info.channel_id)

    elif info.action == AlarmActions.delete:
        await redis.srem(args_key, info.channel_id)
        # delete job if no args left for alarm
        if not await redis.exists(*alarm_args):
            job_id = await redis.hget(rk.alarms_job, info.alarm)
            if not job_id:
                logging.error(f"Job_id for {args_key} wasn't found. Task info: {info}")
                return

            await scheduler.remove_job(job_id)
            await redis.hdel(rk.alarms_job, info.alarm)


async def clean_redis_keys():
    keys_to_del = [
        rk.scheduler_jobs,
        rk.scheduler_runtimes,
        rk.alarms_queue,
        rk.alarms_job,
    ]
    alarms_keys = []
    async with redis_helper.async_connection() as redis:
        alarms_keys = [key async for key in redis.scan_iter("alarms:*:*", _type="set")]
        await redis.unlink(*keys_to_del, *alarms_keys)


async def initialize_scheduler_tasks(scheduler: Scheduler):
    await clean_redis_keys()

    nearest_monday = nearest_weekday(0)
    scheduler.set_timezone(MSK_TIMEZONE_OFFSET)
    await scheduler.add_job(
        weekly_report_task,
        start_date=datetime.combine(nearest_monday, time(hour=23)),
        interval=timedelta(days=7),
    )
    await scheduler.add_job(
        db_cleaner_task,
        start_date=datetime.combine(datetime.today(), time(hour=22)),
        interval=timedelta(days=1),
    )

    users: Iterable[User] = []
    async with db_helper.async_session() as session:
        users = await session.scalars(select(User).where(User.alarm.is_not(None)))

    async with redis_helper.async_connection() as redis:
        for user in users:
            await handle_alarm_task(
                AlarmTaskInfo(
                    AlarmActions.add, Channel(user.channel), user.channel_id, str(user.alarm)
                ),
                scheduler,
                redis,
            )


async def main():
    scheduler = Scheduler(settings.redis)
    await initialize_scheduler_tasks(scheduler)
    await scheduler.start()

    gk = GracefulKiller(raise_ex=True)
    async with redis_helper.async_connection() as redis:
        while not gk.exit_now:
            task_key = await redis.blpop(rk.alarms_queue, 1)
            if not task_key:
                continue

            info = AlarmTaskInfo.from_str(task_key[1])
            if not info:
                logging.error(f"Can't parse task info: {task_key[1]}")
                continue

            await handle_alarm_task(info, scheduler, redis)

    await scheduler.shutdown()


def worker(test_config: bool = False):
    if test_config:
        init_test_settings()

    if platform.system() == "Windows":
        # loop not closes properly on loop.close() by default on windows
        # https://stackoverflow.com/questions/45600579/asyncio-event-loop-is-closed-when-getting-loop
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    loop = asyncio.new_event_loop()
    try:
        loop.run_until_complete(main())
    except GracefulExit:
        logging.info("Worker got termination signal. Shutting down...")

        group = asyncio.gather(*asyncio.all_tasks(loop=loop))
        loop.run_until_complete(group)
        if not loop.is_closed():
            loop.close()
