from contextlib import contextmanager
from typing import AsyncGenerator, Generator
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import sessionmaker, Session


class DatabaseHelper:

    def __init__(self, db_url: str, echo: bool) -> None:
        self.engine = create_engine(url=db_url, echo=echo)
        self.sessionmaker = sessionmaker(bind=self.engine)
        self.async_engine = create_async_engine(url=db_url, echo=echo)
        self.async_sessionmaker = async_sessionmaker(
            bind=self.async_engine,
            autoflush=False,
            autocommit=False,
            expire_on_commit=False,
        )

    async def async_session_dependency(self) -> AsyncGenerator[AsyncSession, None]:
        async with self.async_sessionmaker() as session:
            yield session

    @contextmanager
    def session_context(self) -> Generator[Session, None, None]:
        session = self.sessionmaker()
        try:
            yield session
        finally:
            session.close()
