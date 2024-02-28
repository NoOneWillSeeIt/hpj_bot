from fastapi import APIRouter

from webapp.core.constants import Channel

router = APIRouter(prefix='/webhooks', tags=['webhooks'])


@router.post('/subscribe')
async def subscribe(channel: Channel):
    pass


@router.post('/unsubscribe')
async def unsubscribe(channel: Channel):
    pass
