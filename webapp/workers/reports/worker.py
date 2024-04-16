import json
import logging
import multiprocessing
import os
from concurrent.futures import Future, ProcessPoolExecutor
from datetime import datetime, timedelta
from typing import Sequence

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from common.constants import CERTS_DIR, ENTRY_DATE_FORMAT
from common.survey.hpj_questions import Questions
from common.utils import concat_url, gen_jwt_token
from webapp.core import redis_helper
from webapp.core.db_helper import DatabaseHelper
from webapp.core.models import JournalEntry
from webapp.core.redis import RedisKeys, ReportRequester, ReportTaskInfo
from webapp.core.settings import DbSettings, JinjaSettings, init_test_settings, settings
from webapp.workers.reports.journal_view.html_generator import HTMLGenerator
from webapp.workers.utils import GracefulKiller


class ProcessLocals:
    """Locals for process which should be initialized once and used on every worker call"""

    def __init__(self) -> None:
        self._db_helper: DatabaseHelper | None = None
        self._html_generator: HTMLGenerator | None = None
        self._logger: logging.Logger | None = None
        # default settings
        self._db_settings = settings.db
        self._jinja_settings = settings.jinja
        self._log_level = logging.DEBUG

    def init_settings(
        self, db_settings: DbSettings, jinja_settings: JinjaSettings, log_level: int
    ):
        self._db_settings = db_settings
        self._jinja_settings = jinja_settings
        self._log_level = log_level

    @property
    def db_helper(self) -> DatabaseHelper:
        if not self._db_helper:
            self._db_helper = DatabaseHelper(
                self._db_settings.engine_url,
                self._db_settings.async_engine_url,
                self._db_settings.echo,
            )
        return self._db_helper

    @property
    def html_generator(self) -> HTMLGenerator:
        if not self._html_generator:
            self._html_generator = HTMLGenerator(
                folder_path=self._jinja_settings.templates_dir,
                template_name=self._jinja_settings.journal_tmpl,
                questions=Questions.to_dict(),
            )
        return self._html_generator

    @property
    def logger(self) -> logging.Logger:
        if not self._logger:
            self._logger = multiprocessing.get_logger()
            self._logger.name = f"worker #{os.getpid()}"
            self._logger.setLevel(self._log_level)
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            handler = logging.StreamHandler()
            handler.setFormatter(formatter)
            self._logger.addHandler(handler)
        return self._logger


_pl = ProcessLocals()


def init_process_worker(
    db_settings: DbSettings, jinja_settings: JinjaSettings, log_level: int
):
    _pl.init_settings(db_settings, jinja_settings, log_level)


def read_entries_from_db(
    session: Session, info: ReportTaskInfo
) -> Sequence[JournalEntry]:
    start_dt = datetime.strptime(info.start, ENTRY_DATE_FORMAT)
    end_dt = datetime.strptime(info.end, ENTRY_DATE_FORMAT)
    delta_days = (end_dt - start_dt).days
    report_range = [
        (end_dt - timedelta(days=i)).strftime(ENTRY_DATE_FORMAT)
        for i in range(delta_days + 1)
    ]
    stmt = (
        select(JournalEntry)
        .where(JournalEntry.user_id == info.user_id)
        .where(JournalEntry.date.in_(report_range))
    )
    return session.scalars(stmt).all()


def send_report(url: str, data: dict | None, files: dict | None = None):
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
    report_meta = {
        "channel_id": info.channel_id,
        "requester": info.requester,
        "start_date": info.start,
        "end_date": info.end,
    }

    entry_rows: Sequence[JournalEntry] = []
    with _pl.db_helper.session() as session:
        entry_rows = read_entries_from_db(session, info)

    _pl.logger.debug(f"{len(entry_rows)} rows read from entries.")
    if not entry_rows:
        # if task was created by channel we need to send empty answer
        if info.requester == ReportRequester.channel:
            _pl.logger.debug("Sending empty report.")
            send_report(url, report_meta)
        return

    out_file = _pl.html_generator.generate(
        replies={row.date: json.loads(row.entry) for row in entry_rows},
    )
    filename = _pl.html_generator.gen_filename(f"{info.start}-{info.end}")

    _pl.logger.debug(f"Generated report {filename}, {len(out_file)} bytes")
    send_report(
        url, report_meta, files={"file": (filename, out_file, "multipart/form-data")}
    )
    _pl.logger.info(f"Report for {info.user_id} was sended")


def future_done_callback(fut: Future):
    if fut.exception():
        logging.error(fut.exception())


def worker(worker_count: int = 4, test_config: bool = False):

    log_level = logging.getLogger().level
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
            if not channel_url:
                logging.error(
                    f"No url registered for {info.channel}, but report was requested"
                )
                continue

            future = pool.submit(
                generate_report, info, concat_url(channel_url, "reports")
            )
            future.add_done_callback(future_done_callback)

        logging.info(f"Stopping workers by signal: {gk.signum}")
        pool.shutdown(wait=True)
