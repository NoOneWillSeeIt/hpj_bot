import json
import logging
import multiprocessing
import os
from concurrent.futures import Future, ProcessPoolExecutor
from datetime import datetime, timedelta

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from common.constants import CERTS_DIR, ENTRY_DATE_FORMAT
from common.survey.hpj_questions import Questions
from common.utils import concat_url, gen_jwt_token
from webapp.core import redis_helper
from webapp.core.db_helper import DatabaseHelper
from webapp.core.models import JournalEntry
from webapp.core.redis import RedisKeys, ReportTaskInfo, ReportTaskProducer
from webapp.core.settings import DbSettings, JinjaSettings, init_test_settings, settings
from webapp.workers.reports.journal_view.html_generator import HTMLGenerator
from webapp.workers.utils import GracefulKiller


class ProcessLocals:
    """Locals for process which should be initialized once and used on every worker call"""

    db_helper: DatabaseHelper | None = None
    html_generator: HTMLGenerator | None = None
    logger: logging.Logger | None = None


_pl = ProcessLocals()


def init_process_worker(
    db_settings: DbSettings, jinja_settings: JinjaSettings, log_level: int
):
    _pl.db_helper = DatabaseHelper(
        db_settings.engine_url, db_settings.async_engine_url, db_settings.echo
    )

    _pl.html_generator = HTMLGenerator(
        folder_path=jinja_settings.templates_dir,
        template_name=jinja_settings.journal_tmpl,
        questions=Questions.to_dict(),
    )

    logger = multiprocessing.get_logger()
    logger.name = f"worker #{os.getpid()}"
    logger.setLevel(log_level)
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    _pl.logger = logger


def read_entries_from_db(session: Session, info: ReportTaskInfo) -> list[JournalEntry]:
    start_dt = datetime.strptime(info.start, ENTRY_DATE_FORMAT)
    end_dt = datetime.strptime(info.end, ENTRY_DATE_FORMAT)
    delta_days = (end_dt - start_dt).days
    report_range = [
        (end_dt - timedelta(days=i)).strftime(ENTRY_DATE_FORMAT)
        for i in range(delta_days)
    ]
    stmt = (
        select(JournalEntry)
        .where(JournalEntry.user_id == info.user_id)
        .where(JournalEntry.date.in_(report_range))
    )
    return session.scalars(stmt).all()


def send_report(url: str, data: dict | None, files: dict | None):
    httpx.post(
        url=url,
        data=data,
        files=files,
        headers={
            "Authorization": "Bearer "
            + gen_jwt_token({"issuer": "webapp", "reason": "alarms"})
        },
        verify=str(CERTS_DIR / "ssl-cert.pem"),
    )


def generate_report(info: ReportTaskInfo, url: str):
    entry_rows = []
    with _pl.db_helper.session() as session:
        entry_rows = read_entries_from_db(session, info)

    _pl.logger.debug(f"{len(entry_rows)} rows read from entries.")
    if not entry_rows:
        # if task was created by channel we need to send empty answer
        if info.producer == ReportTaskProducer.channel:
            _pl.logger.debug("Sending empty report.")
            send_report(url, data={"channel_id": info.channel_id})
        return

    out_file = _pl.html_generator.generate(
        replies={row.date: json.loads(row.entry) for row in entry_rows},
    )
    filename = _pl.html_generator.gen_filename(f"{info.start}-{info.end}")

    _pl.logger.debug(f"Generated report {filename}, {len(out_file)} bytes")
    send_report(
        url,
        data={"channel_id": info.channel_id},
        files={"file": (filename, out_file, "multipart/form-data")},
    )
    _pl.logger.info(f"Report for {info.user_id} was sended")


def future_done_callback(fut: Future):
    if fut.exception():
        logging.error(fut.exception())


def worker(worker_count: int = 4, test_config: bool = False):

    log_level = logging.INFO
    if test_config:
        log_level = logging.DEBUG
        init_test_settings()

    with (
        ProcessPoolExecutor(
            worker_count,
            initializer=init_process_worker,
            initargs=(settings.db, settings.jinja, log_level),
        ) as pool,
        redis_helper.connection() as redis,
    ):
        gk = GracefulKiller()
        logging.info("Ready to pickup tasks")
        while not gk.exit_now:
            task_key = redis.blpop([RedisKeys.reports_queue], timeout=1)
            if not task_key:
                continue

            info = ReportTaskInfo.from_str(task_key[1])
            if not info:
                logging.error(f'Can\'t parse task info: "{task_key[1]}"')
                continue

            channel_url = redis.get(RedisKeys.webhooks_url(info.channel))

            future = pool.submit(
                generate_report, info, concat_url(channel_url, "reports")
            )
            future.add_done_callback(future_done_callback)

        logging.info(f"Stopping workers by signal: {gk.signum}")
        pool.shutdown(wait=True)
