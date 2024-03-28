from datetime import datetime, timedelta, timezone
from typing import Annotated, Any

import httpx
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from common.constants import AuthSettings

http_bearer = HTTPBearer()


def concat_url(url1: httpx.URL | str, url2: httpx.URL | str) -> str:
    return str(httpx.URL(url1).join(url2))


def gen_jwt_token(payload: dict[str, Any], auth_settings: AuthSettings):
    to_encode = payload.copy()
    to_encode["exp"] = datetime.now(timezone.utc) + timedelta(
        seconds=auth_settings.expire_seconds
    )

    return jwt.encode(
        to_encode, auth_settings.private_key.read_bytes(), auth_settings.algorithm
    )


class DepAttrMeta(type):

    attr: Any = None

    def __call__(cls, *args, **kwargs) -> Any:
        return cls.attr


class AuthSettingsDependency(metaclass=DepAttrMeta):

    attr: AuthSettings = AuthSettings()

    @classmethod
    def set_new(cls, stg: AuthSettings):
        cls.attr = stg


async def check_jwt_token_dep(
    auth_settings: Annotated[AuthSettings, Depends(AuthSettingsDependency)],
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(http_bearer)],
):
    try:
        payload = jwt.decode(
            credentials.credentials,
            auth_settings.public_key.read_bytes(),
            [auth_settings.algorithm],
        )
    except jwt.ExpiredSignatureError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid token")

    return payload
