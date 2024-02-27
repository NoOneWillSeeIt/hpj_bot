from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import ExpiredSignatureError

from webapp.core import settings

security = HTTPBearer()


def decode_jwt(jwt_token: str, pub_key: str, algorithm: str) -> dict:
    return jwt.decode(jwt_token, pub_key, algorithms=[algorithm])


async def check_token_dep(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)]
):
    try:
        decode_jwt(
            credentials.credentials, settings.auth.pub_key, settings.auth.algorithm
        )
    except ExpiredSignatureError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid token")
