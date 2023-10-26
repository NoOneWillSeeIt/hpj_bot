import asyncio
import os
from typing import Any
from unittest import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock

from telegram.ext import ConversationHandler

from tests.utils.common import create_test_db
from tests.utils.ptb_app import TEST_PERSISTENCE_NAME, make_app


class AsyncResultCacheMock(AsyncMock):

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._result_cache = []

    async def __call__(self, *args: Any, **kwargs: Any) -> Any:
        call_result = super().__call__(*args, **kwargs)
        if asyncio.iscoroutine(call_result):
            result = await call_result
        else:
            result = call_result
        self._result_cache.append(result)
        return result

    @property
    def result_cache(self):
        return self._result_cache


class AsyncDBTestCase(IsolatedAsyncioTestCase):

    async def asyncSetUp(self) -> None:
        db_path, conn = await create_test_db()
        self.conn = conn
        self.bot_data = {
            'db_conn': conn,
            'db_path': db_path,
        }
        return await super().asyncSetUp()

    async def asyncTearDown(self) -> None:
        await self.conn.close()
        return await super().asyncTearDown()


class AsyncTelegramBotTestCase(AsyncDBTestCase):

    _handlers = []

    async def asyncSetUp(self) -> None:
        await super().asyncSetUp()
        self.app = make_app()
        self.app.add_handlers(self._handlers)
        self.app.bot_data.update(self.bot_data)
        self.app.bot._unfreeze()
        await self.app.initialize()

    async def asyncTearDown(self) -> None:
        await self.app.shutdown()

        for handler in self._handlers:
            if isinstance(handler, ConversationHandler):
                handler._conversations.clear()

        if os.path.isfile(TEST_PERSISTENCE_NAME):
            os.remove(TEST_PERSISTENCE_NAME)
        return await super().asyncTearDown()
