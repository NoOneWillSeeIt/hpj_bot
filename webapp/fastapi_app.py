from contextlib import asynccontextmanager
from fastapi import FastAPI

from webapp.api_v1 import APIv1_Router
from webapp.core import db_helper
from webapp.core.models import Base


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with db_helper.engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield

app = FastAPI(lifespan=lifespan)
app.include_router(APIv1_Router)
