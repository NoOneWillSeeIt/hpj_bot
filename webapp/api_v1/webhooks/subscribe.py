from fastapi import APIRouter
from pydantic import BaseModel

from webapp.api_v1.common_dependencies import RedisDep
from webapp.core.constants import Channel
from webapp.core.redis import RedisKeys

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


class SubscribeSchema(BaseModel):
    channel: Channel
    url: str


@router.post("/subscribe")
async def subscribe(body: SubscribeSchema, redis: RedisDep):
    await redis.set(RedisKeys.webhooks_url(body.channel), body.url)
