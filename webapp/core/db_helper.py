from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession


class DatabaseHelper:

    def __init__(self, db_url: str, echo: bool) -> None:
        self.engine = create_async_engine(url=db_url, echo=echo)
        self.sessionmaker = async_sessionmaker(
            bind=self.engine,
            autoflush=False,
            autocommit=False,
            expire_on_commit=False,
        )

    async def async_session_dependency(self) -> AsyncSession:
        async with self.sessionmaker() as session:
            yield session
