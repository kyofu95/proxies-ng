from typing import Annotated
from uuid import UUID

from fastapi import Depends, Request

from app.core.database import async_session_factory
from app.core.exceptions import TokenError
from app.core.security import JWT
from app.core.uow import SQLUnitOfWork
from app.service.user import UserService


def get_user_service() -> UserService:
    """
    Dependency function that provides an instance of UserService.

    Creates a new SQLUnitOfWork using the async session factory
    and returns a UserService that uses this UoW.

    Returns:
        UserService: An instance of UserService with a unit of work.
    """
    # TODO(sny): this function already exists in /api
    uow = SQLUnitOfWork(async_session_factory)
    return UserService(uow)


UserServiceDep = Annotated[UserService, Depends(get_user_service)]
"""Dependency for providing an instance of UserService."""


async def is_logged_in(request: Request, user_service: UserServiceDep) -> bool:
    """
    Check whether the current request has a valid logged-in user via cookie token.

    Args:
        request (Request): The current HTTP request, used to access cookies.
        user_service (UserServiceDep): The user service for verifying the user by token.

    Returns:
        bool: True if a valid access token exists and corresponds to a known user, False otherwise.
    """
    access_token = request.cookies.get("access_token")
    if not access_token:
        return False

    try:
        user_id = JWT.decode(access_token)
    except TokenError:
        return False

    user = await user_service.get_by_id(UUID(user_id))
    if not user:  # noqa: SIM103
        return False
    return True


IsLoggedDep = Annotated[bool, Depends(is_logged_in)]
"""Annotated dependency that returns True if a user is authenticated, otherwise False."""
