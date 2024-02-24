__all__ = (
    "SessionDep",
    "FindUserBodyDep",
    "SessionDep",
)


from typing import Annotated

from fastapi import Depends

from webapp.api_v1.common_dependencies.session_deps import SessionDep
from webapp.api_v1.common_dependencies.user_deps import (
    ensure_user_body_dep,
    find_user_query_dep,
)
from webapp.core.models import User

FindUserQueryDep = Annotated[User | None, Depends(find_user_query_dep)]
EnsureUserBodyDep = Annotated[User | None, Depends(ensure_user_body_dep)]
