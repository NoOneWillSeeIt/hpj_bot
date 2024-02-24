__all__ = ("APIv1_Router",)


from fastapi import APIRouter

from webapp.api_v1.alarm import AlarmRouter
from webapp.api_v1.entries import EntriesRouter
from webapp.core.settings import settings

APIv1_Router = APIRouter(prefix=settings.api_v1_prefix)
APIv1_Router.include_router(AlarmRouter)
APIv1_Router.include_router(EntriesRouter)
