from pydantic import BaseModel

from webapp.core.constants import Channel


class UserChannelSchema(BaseModel):
    channel: Channel
    channel_id: int


class UserMixinSchema(BaseModel):
    user: UserChannelSchema
