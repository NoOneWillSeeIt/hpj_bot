from contextlib import asynccontextmanager, contextmanager
from typing import AsyncGenerator, Generator
from redis import Redis
from redis.asyncio import Redis as AsyncRedis


class RedisHelper:

    def __init__(self, host: str, port: int, db: int):
        self.redis = Redis(host, port, db)
        self.async_redis = AsyncRedis(host=host, port=port, db=db)

    @asynccontextmanager
    async def async_connection(self) -> AsyncGenerator[AsyncRedis, None]:
        conn = AsyncRedis(connection_pool=self.async_redis.connection_pool)
        try:
            yield conn
        finally:
            await conn.aclose()

    @contextmanager
    def connection(self) -> Generator[Redis, None, None]:
        conn = Redis(connection_pool=self.redis)
        try:
            yield conn
        finally:
            conn.close()

    async def async_redis_dependency(self) -> AsyncGenerator[AsyncRedis, None]:
        async with self.async_connection() as conn:
            yield conn
