import json
import logging
import multiprocessing
from concurrent.futures import ProcessPoolExecutor

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from common.constants import ReportTaskProducer
from common.survey.hpj_questions import Questions
from common.utils import concat_url
from webapp.core import redis_helper
from webapp.core.db_helper import DatabaseHelper
from webapp.core.models import JournalEntry
from webapp.core.redis import RedisKeys, ReportTaskInfo
from webapp.core.settings import DbSettings, JinjaSettings, init_test_settings, settings
from webapp.workers.reports.journal_view.html_generator import HTMLGenerator
from webapp.workers.utils import GracefulKiller

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


def read_entries_from_db(session: Session, info: ReportTaskInfo) -> list[JournalEntry]:
    stmt = (
        select(JournalEntry)
        .where(JournalEntry.user_id == info.user_id)
        .where(info.start <= JournalEntry.date <= info.end)
    )
    return session.scalars(stmt).all()


def generate_report(info: ReportTaskInfo, url_to_send: str):
    entry_rows = []
    with _process_db_helper.session() as session:
        entry_rows = read_entries_from_db(session, info)

    if not entry_rows:
        # if task was created by channel we need to send empty answer
        if info.producer == ReportTaskProducer.channel:
            httpx.post(
                url=url_to_send,
                data={"channel_id": info.channel_id},
            )
        return

    out_file = _process_html_generator.generate(
        replies={row.date: json.loads(row.entry) for row in entry_rows},
    )
    filename = _process_html_generator.gen_filename(f"{info.start}-{info.end}")

    httpx.post(
        url=url_to_send,
        data={"channel_id": info.channel_id},
        files={"file": (filename, out_file, "multipart/form-data")},
    )


def worker(worker_count: int = 4, test_config: bool = False):

    if test_config:
        init_test_settings()

    with (
        ProcessPoolExecutor(
            worker_count,
            initializer=init_process_worker,
            initargs=(settings.db, settings.jinja),
        ) as pool,
        redis_helper.connection() as redis,
    ):
        gk = GracefulKiller()
        while not gk.exit_now:
            task_key = redis.blpop([RedisKeys.reports_queue], timeout=1)
            if not task_key:
                continue

            info = ReportTaskInfo.from_str(task_key)
            if not info:
                logging.error(f'Can\'t parse task info: "{info}"')
                continue

            channel_url = redis.get(RedisKeys.webhooks_url(info.channel))
            pool.submit(generate_report, info, concat_url(channel_url, "reports"))

        logging.log(f"Stopping workers by signal: {gk.signum}")
        pool.shutdown(wait=True)
