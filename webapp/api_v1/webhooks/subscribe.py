from fastapi import APIRouter
from pydantic import BaseModel

from webapp.api_v1.common_dependencies import RedisDep
from common.constants import Channel
from webapp.core.redis import RedisKeys

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


class WebhookSchema(BaseModel):
    channel: Channel


class UnsubSchema(WebhookSchema):
    pass


class SubscribeSchema(WebhookSchema):
    url: str


@router.post("/subscribe")
async def subscribe(body: SubscribeSchema, redis: RedisDep):
    await redis.set(RedisKeys.webhooks_url(body.channel), body.url)


@router.post("/unsubscribe")
async def unsubscribe(body: UnsubSchema, redis: RedisDep):
    await redis.delete(RedisKeys.webhooks_url(body.channel))
