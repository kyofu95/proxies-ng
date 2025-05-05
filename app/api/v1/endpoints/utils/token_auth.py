from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, Request, status

from app.core.exceptions import TokenError
from app.core.security import JWT
from app.models.user import User

from .dependencies import UserServiceDep


async def get_user_from_token(token: str, user_service: UserServiceDep) -> User:
    """
    Retrieve a user from the given token.

    Args:
        token (str): The JWT access or refresh token provided by the user.
        user_service (UserServiceDep): The user service dependency for accessing user data.
        token_type (str): The expected type of the token. Must be either "access" or "refresh".

    Returns:
        User: The user entity associated with the token.

    Raises:
        HTTPException: If the token is invalid, expired, or if the user cannot be found.
    """
    try:
        user_id = JWT.decode(token)
    except TokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    user = await user_service.get_by_id(UUID(user_id))
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authorized.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


async def get_current_user_from_cookie(request: Request, user_service: UserServiceDep) -> User:
    """
    Retrieve the current user from a cookie-stored access token.

    Args:
        request (Request): The current HTTP request, used to access cookies.
        user_service (UserServiceDep): The user service dependency for accessing user data.

    Returns:
        User: The user entity associated with the access token from the cookie.

    Raises:
        HTTPException: If the access token is missing or invalid.
    """
    access_token = request.cookies.get("access_token")
    if not access_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authorized.")
    return await get_user_from_token(access_token, user_service)


CurrentUserDep = Annotated[User, Depends(get_current_user_from_cookie)]
"""Annotated dependency for retrieving the current authenticated user from the access token cookie."""
