from pydantic import BaseModel

from common.constants import Channel


class UserChannelSchema(BaseModel):
    channel: Channel
    channel_id: int


class UserMixinSchema(BaseModel):
    user: UserChannelSchema
