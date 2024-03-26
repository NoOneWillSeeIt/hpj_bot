from collections import namedtuple
from enum import StrEnum, auto
from typing import Any, Self

from common.constants import Channel


class RedisKeys:

    # str
    __webhooks_url = "webhooks:{}-url"

    # hmap
    scheduler_jobs = "scheduler:jobs"  # job_id: pickled job
    alarms_job = "alarms:jobs"  # time: job_id

    # sorted set
    scheduler_runtimes = "scheduler:runtimes"  # job_id: timestamp

    # list
    alarms_queue = "alarms:queue"
    reports_queue = "reports:queue"

    # set
    __alarms_users = "alarms:{}:{}"  # users subbed to alarm

    @classmethod
    def alarms_users(cls, channel: str, time: str) -> str:
        return cls.__alarms_users.format(channel, time)

    @classmethod
    def webhooks_url(cls, channel: str) -> str:
        return cls.__webhooks_url.format(channel)


class ReportTaskProducer(StrEnum):
    channel = auto()
    scheduler = auto()


class AlarmActions(StrEnum):
    add = auto()
    delete = auto()


_ReportTaskInfo = namedtuple(
    "_ReportTaskInfo",
    ["user_id", "channel", "channel_id", "producer", "start", "end"],
)


_AlarmTaskInfo = namedtuple(
    "_AlarmTaskInfo",
    ["action", "channel", "channel_id", "alarm"],
)


class TaskInfo:

    @classmethod
    def from_str(cls, info: str) -> Self | None:
        raise NotImplementedError

    def to_str(self, sep=";") -> str:
        return sep.join(
            [str(getattr(self, field)) for field in getattr(self, "_fields")]
        )


class ReportTaskInfo(_ReportTaskInfo, TaskInfo):

    def __init__(
        self,
        user_id: int,
        channel: Channel,
        channel_id: int,
        producer: ReportTaskProducer,
        start: str,
        end: str,
    ): ...

    @classmethod
    def from_str(cls, info: str) -> Self | None:
        try:
            splitted: list[Any] = info.split(";")
            splitted[0] = int(splitted[0])  # user_id
            splitted[1] = Channel(splitted[1])  # channel
            splitted[2] = int(splitted[2])  # channel_id
            splitted[3] = ReportTaskProducer(splitted[3])  # producer

            return cls(*splitted)
        except Exception:
            pass

        return None


class AlarmTaskInfo(_AlarmTaskInfo, TaskInfo):

    def __init__(
        self, action: AlarmActions, channel: Channel, channel_id: int, alarm: str
    ): ...

    @classmethod
    def from_str(cls, info: str) -> Self | None:
        try:
            splitted: list[Any] = info.split(";")
            splitted[0] = AlarmActions(splitted[0])  # action
            splitted[1] = Channel(splitted[1])  # channel
            splitted[2] = int(splitted[2])  # channel_id

            return cls(*splitted)
        except Exception:
            pass

        return None
