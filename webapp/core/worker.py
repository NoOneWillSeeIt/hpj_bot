import json
import logging
import multiprocessing
import signal
from collections import namedtuple
from concurrent.futures import ProcessPoolExecutor

import requests
from redis import Redis
from sqlalchemy import select
from sqlalchemy.orm import Session

from survey.hpj_questions import Questions
from webapp.core.constants import Channel, ReportTaskProducer
from webapp.core.db_helper import DatabaseHelper
from webapp.core.models import JournalEntry
from webapp.journal_view.html_generator import HTMLGenerator

from .settings import DbSettings, JinjaSettings, init_test_settings, settings

TaskInfo = namedtuple(
    "TaskInfo",
    ["user_id", "channel", "channel_id", "producer", "start", "end"],
    defaults=[None] * 6,
)


class GracefulKiller:

    exit_now = False
    signum = None

    def __init__(self):
        for sig_code in [signal.SIGINT, signal.SIGTERM]:
            signal.signal(sig_code, self.handle_signal)

    def handle_signal(self, signum, frame):
        self.exit_now = True
        self.signum = signum


_process_db_helper: DatabaseHelper | None = None
_process_html_generator: HTMLGenerator | None = None
_process_logger: logging.Logger | None = None


def init_process_worker(db_settings: DbSettings, jinja_settings: JinjaSettings):
    global _process_db_helper, _process_html_generator, _process_logger
    _process_db_helper = DatabaseHelper(db_settings.url, db_settings.echo)
    _process_html_generator = HTMLGenerator(
        folder_path=jinja_settings.templates_dir,
        template_name=jinja_settings.journal_tmpl,
        questions=Questions.to_dict(),
    )
    _process_logger = multiprocessing.get_logger()


def read_entries_from_db(session: Session, info: TaskInfo) -> list[JournalEntry]:
    stmt = (
        select(JournalEntry)
        .where(JournalEntry.user_id == info.user_id)
        .where(info.start <= JournalEntry.date <= info.end)
    )
    return session.scalars(stmt).all()


def parse_task_info(task_info: str) -> TaskInfo:
    try:
        splitted = task_info.split(";")
        splitted[0] = int(splitted[0])  # user_id
        splitted[1] = Channel(splitted[1])  # channel
        splitted[2] = int(splitted[2])  # channel_id
        splitted[3] = ReportTaskProducer(splitted[3])  # producer

        return TaskInfo(*splitted)
    except Exception:
        logging.error(f'Can\'t parse task info: "{task_info}"')

    return TaskInfo()


def worker(info: TaskInfo, url_to_send: str):
    entry_rows = []
    with _process_db_helper.session_context() as session:
        entry_rows = read_entries_from_db(session, info)

    if not entry_rows:
        if info.producer == ReportTaskProducer.channel:
            # TODO: return that no entries found if user asked for them
            pass
        else:
            return

    out_file = _process_html_generator.generate(
        replies={row.date: json.loads(row.entry) for row in entry_rows},
    )
    filename = _process_html_generator.gen_filename(f"{info.start}-{info.end}")

    requests.post(
        url=url_to_send,
        files={"upload_file": (filename, out_file, "multipart/form-data")},
    )


def pool_handler(worker_count: int = 4, test_config: bool = False):

    if test_config:
        init_test_settings()

    redis = Redis(host=settings.redis.url, port=settings.redis.port)
    with ProcessPoolExecutor(
        worker_count,
        initializer=init_process_worker,
        initargs=(settings.db, settings.jinja),
    ) as pool:
        gk = GracefulKiller()
        while not gk.exit_now:
            task_key = redis.blpop(["gen_report_queue"], timeout=1)
            if not task_key:
                continue

            info = parse_task_info(task_key)
            channel_url = redis.get(f"{info.channel}_url")
            pool.submit(worker, info, f"{channel_url}/{info.channel_id}")

        logging.log(f"Stopping workers by signal: {gk.signum}")
        pool.shutdown(wait=True)
