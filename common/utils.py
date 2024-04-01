from datetime import datetime, timedelta, timezone
from functools import reduce
from typing import Annotated, Any

import httpx
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from common.constants import AuthSettings as Auth

http_bearer = HTTPBearer()


def concat_url(url: httpx.URL | str, *endpoints: httpx.URL | str) -> str:
    def concat_two(url1: str, url2: httpx.URL | str) -> str:
        if not url1.endswith("/"):
            url1 += "/"
        return str(httpx.URL(url1).join(url2))

    return str(reduce(concat_two, endpoints, str(url)))


def gen_jwt_token(payload: dict[str, Any]):
    to_encode = payload.copy()
    to_encode["exp"] = datetime.now(timezone.utc) + timedelta(
        seconds=Auth.expire_seconds
    )

    return jwt.encode(to_encode, Auth.private_key, Auth.algorithm)


async def check_jwt_token_dep(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(http_bearer)],
):
    try:
        payload = jwt.decode(
            credentials.credentials,
            Auth.public_key,
            [Auth.algorithm],
        )
    except jwt.ExpiredSignatureError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid token")

    return payload
