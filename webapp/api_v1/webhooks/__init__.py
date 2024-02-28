__all__ = (
    "WebhooksRouter",
    "WebHooksOpenApiDocsRouter",
)

from .hooks import router as WebHooksOpenApiDocsRouter
from .subscribe import router as WebhooksRouter
