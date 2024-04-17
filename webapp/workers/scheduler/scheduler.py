import asyncio
import logging
import math
import pickle
from datetime import datetime, timedelta, tzinfo
from uuid import uuid4

import redis.asyncio as redis

from webapp.core.redis import RedisKeys
from webapp.core.settings import RedisSettings

logger = logging.getLogger("Scheduler")


class FireCondition:

    def __init__(
        self,
        start: datetime | None,
        interval: timedelta | None,
        *,
        offset: tzinfo | None = None,
    ) -> None:
        self.offset = offset
        self.start = start if start else datetime.now(self.offset)
        self.interval = interval

    def __getstate__(self) -> object:
        return {
            "start_date": self.start,
            "interval": self.interval,
            "offset": self.offset,
        }

    def __setstate__(self, state):
        self.start = state["start_date"]
        self.interval = state["interval"]
        self.offset = state["offset"]

    def __repr__(self) -> str:
        return (
            f"FireCond(start={self.start}, "
            f"interval={self.interval}, offset={self.offset})"
        )

    def get_next_fire_time(self, date: datetime | None = None) -> datetime | None:
        date = date or datetime.now(self.offset)
        if self.start > date:
            return self.start

        if not self.interval:
            return None

        timediff = (date - self.start).total_seconds()
        intervals_num = int(math.ceil(timediff / self.interval.total_seconds()))
        return self.start + self.interval * intervals_num


class Job:

    def __init__(self, func, args, kwargs, fire_condition: FireCondition):
        self.id = str(uuid4())
        self.func = func
        self.args = args
        self.kwargs = kwargs
        self.fire_cond = fire_condition

    def __getstate__(self):
        func_ref = self.func.__module__ + ":" + self.func.__qualname__
        return {
            "id": self.id,
            "func": func_ref,
            "args": self.args,
            "kwargs": self.kwargs,
            "fire_cond": self.fire_cond,
        }

    def __setstate__(self, state):
        self.id = state["id"]
        module, func_name = state["func"].split(":", 1)
        module_obj = __import__(module, fromlist=[func_name])
        self.func = getattr(module_obj, func_name)
        self.args = state["args"]
        self.kwargs = state["kwargs"]
        self.fire_cond = state["fire_cond"]

    def __repr__(self) -> str:
        return f"Job(id={self.id}, func={self.func.__qualname__}, fire_cond={repr(self.fire_cond)})"

    def get_coro(self):
        return self.func(*self.args, **self.kwargs)

    def get_next_fire_time(self, date: datetime | None = None) -> datetime | None:
        return self.fire_cond.get_next_fire_time(date)


class Scheduler:

    __jobs_key = RedisKeys.scheduler_jobs
    __jobs_runtimes = RedisKeys.scheduler_runtimes
    __delay: int = 1

    def __init__(self, redis_settings: RedisSettings):
        self.redis = redis.Redis(
            host=redis_settings.host, port=redis_settings.port, db=redis_settings.db
        )
        self._eventloop: asyncio.AbstractEventLoop = None  # type: ignore
        self._offset: tzinfo | None = None
        self._running_tasks: set[asyncio.Task] = set()
        self._active = False

    def set_timezone(self, offset: tzinfo):
        self._offset = offset

    async def add_job(
        self,
        func: object,
        args: list | None = None,
        kwargs: dict | None = None,
        start_date: datetime | None = None,
        interval: timedelta | None = None,
    ) -> Job:
        if args is None:
            args = []

        if kwargs is None:
            kwargs = {}

        if start_date and start_date.tzinfo is None and self._offset is not None:
            start_date = start_date.replace(tzinfo=self._offset)

        now = datetime.now(self._offset)
        fire_cond = FireCondition(start_date, interval, offset=self._offset)
        job = Job(func, args, kwargs, fire_cond)
        async with self.redis.pipeline() as pipe:
            pipe.multi()
            pipe.hset(self.__jobs_key, job.id, pickle.dumps(job))
            pipe.zadd(
                self.__jobs_runtimes,
                {job.id: (job.get_next_fire_time(now) or now).timestamp()},
            )
            await pipe.execute()

        logger.info(f"New job {repr(job)} was added")
        return job

    async def remove_job(self, job: Job | str):
        job_id = job if isinstance(job, str) else job.id
        if not await self.redis.hexists(self.__jobs_key, job_id):
            return

        async with self.redis.pipeline() as pipe:
            pipe.multi()
            pipe.hdel(self.__jobs_key, job_id)
            pipe.zrem(self.__jobs_runtimes, job_id)
            await pipe.execute()

        logger.info(f"Job {repr(job)} was removed")

    async def start(self):
        self._active = True
        self._eventloop = asyncio.get_running_loop()
        self._task = self._eventloop.create_task(self._process_jobs())
        logger.info("Starting scheduler")

    async def stop(self):
        self._active = False
        logger.info("Stopping scheduler")

    async def shutdown(self):
        self._active = False
        await self._task
        logger.info("Shutting down scheduler. Waiting for tasks to finish")
        if self._running_tasks:
            await asyncio.wait(self._running_tasks)

    async def _get_jobs(self, date: datetime) -> list[Job]:
        jobs_ids = await self.redis.zrangebyscore(
            self.__jobs_runtimes, 0, date.timestamp()
        )
        if not jobs_ids:
            return []

        jobs = []
        jobs_data = await self.redis.hmget(self.__jobs_key, jobs_ids)
        for job_id, job_data in zip(jobs_ids, jobs_data):
            if not job_data:
                logger.error(f"No job data was found for job {job_id!r}")
                await self.redis.zrem(self.__jobs_runtimes, job_id)
                continue

            job_obj = pickle.loads(job_data)
            jobs.append(job_obj)

        return jobs

    def _run_job(self, job: Job):
        def callback(task: asyncio.Task):
            self._running_tasks.discard(task)
            if ex := task.exception():
                logger.error(
                    f"Unhandled exception occured while {repr(job)} was running: ",
                    exc_info=ex,
                )

        task = self._eventloop.create_task(job.get_coro())
        self._running_tasks.add(task)
        task.add_done_callback(callback)

    async def _enqueue_job_repeat(self, jobs: list[Job], date: datetime):
        async with self.redis.pipeline() as pipe:
            pipe.multi()
            for job in jobs:
                next_time = job.get_next_fire_time(date)
                if next_time:
                    pipe.zadd(self.__jobs_runtimes, {job.id: next_time.timestamp()})
                else:
                    pipe.zrem(self.__jobs_runtimes, job.id)

            await pipe.execute()

    async def _process_jobs(self):
        while self._active:
            now = datetime.now(self._offset)
            jobs = await self._get_jobs(now)
            for job in jobs:
                self._run_job(job)

            await self._enqueue_job_repeat(jobs, now)
            await asyncio.sleep(self.__delay)
