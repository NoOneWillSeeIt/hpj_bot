__all__ = ("APIv1_Router", "WebHooksOpenApiDocsRouter")


from fastapi import APIRouter

from webapp.core.settings import settings

from .alarm import AlarmRouter
from .entries import EntriesRouter
from .webhooks import WebHooksOpenApiDocsRouter, WebhooksRouter

APIv1_Router = APIRouter(prefix=settings.api_v1_prefix)
APIv1_Router.include_router(AlarmRouter)
APIv1_Router.include_router(EntriesRouter)
APIv1_Router.include_router(WebhooksRouter)
