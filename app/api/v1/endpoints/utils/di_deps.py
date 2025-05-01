from typing import Annotated

from fastapi import Depends

from app.core.database import async_session_factory
from app.core.uow import SQLUnitOfWork
from app.service.proxy import ProxyService
from app.service.user import UserService


def get_proxy_service() -> ProxyService:
    """
    Dependency function that provides an instance of ProxyService.

    Creates a new SQLUnitOfWork using the async session factory
    and returns a ProxyService that uses this UoW.

    Returns:
        ProxyService: An instance of ProxyService with a unit of work.
    """
    uow = SQLUnitOfWork(async_session_factory)
    return ProxyService(uow)


ProxyServiceDep = Annotated[ProxyService, Depends(get_proxy_service)]
"""Dependency for providing an instance of ProxyService."""


def get_user_service() -> UserService:
    """
    Dependency function that provides an instance of UserService.

    Creates a new SQLUnitOfWork using the async session factory
    and returns a UserService that uses this UoW.

    Returns:
        UserService: An instance of UserService with a unit of work.
    """
    uow = SQLUnitOfWork(async_session_factory)
    return UserService(uow)


UserServiceDep = Annotated[UserService, Depends(get_user_service)]
"""Dependency for providing an instance of UserService."""
