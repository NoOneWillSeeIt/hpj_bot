from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI

from common.utils import check_jwt_token_dep
from webapp.api_v1 import APIv1_Router, WebHooksOpenApiDocsRouter
from webapp.core import db_helper
from webapp.core.models import Base


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with db_helper.async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


app = FastAPI(
    lifespan=lifespan,
    dependencies=[Depends(check_jwt_token_dep)],
    webhooks=WebHooksOpenApiDocsRouter,
)
app.include_router(APIv1_Router)
