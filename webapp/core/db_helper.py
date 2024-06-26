from contextlib import asynccontextmanager, contextmanager
from typing import AsyncGenerator, Generator

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import Session, sessionmaker


class DatabaseHelper:

    def __init__(self, db_url: str, async_db_url: str, echo: bool) -> None:
        self.engine = create_engine(url=db_url, echo=echo)
        self.sessionmaker = sessionmaker(
            bind=self.engine, autoflush=False, autocommit=False, expire_on_commit=False
        )
        self.async_engine = create_async_engine(url=async_db_url, echo=echo)
        self.async_sessionmaker = async_sessionmaker(
            bind=self.async_engine,
            autoflush=False,
            autocommit=False,
            expire_on_commit=False,
        )

    @asynccontextmanager
    async def async_session(self) -> AsyncGenerator[AsyncSession, None]:
        session = self.async_sessionmaker()
        try:
            yield session
        finally:
            await session.aclose()

    async def async_session_dependency(self) -> AsyncGenerator[AsyncSession, None]:
        async with self.async_sessionmaker() as session:
            yield session

    @contextmanager
    def session(self) -> Generator[Session, None, None]:
        session = self.sessionmaker()
        try:
            yield session
        finally:
            session.close()
