from typing import Annotated

from fastapi import Depends

from app.core.database import async_session_factory
from app.core.uow import SQLUnitOfWork
from app.service.proxy import ProxyService
from app.service.source import SourceService
from app.service.user import UserService


def get_uow() -> SQLUnitOfWork:
    """
    Dependency provider for SQLUnitOfWork.

    Initializes a SQLUnitOfWork using the asynchronous session factory.

    Returns:
        SQLUnitOfWork: A unit of work instance for database operations.
    """
    return SQLUnitOfWork(async_session_factory)


UnitOfWorkDep = Annotated[SQLUnitOfWork, Depends(get_uow)]
"""Dependency for providing a SQLUnitOfWork instance."""


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


def get_source_service() -> SourceService:
    """
    Dependency function that provides an instance of SourceService.

    Creates a new SQLUnitOfWork using the async session factory
    and returns a SourceService that uses this UoW.

    Returns:
        SourceService: An instance of SourceService with a unit of work.
    """
    uow = SQLUnitOfWork(async_session_factory)
    return SourceService(uow)


SourceServiceDep = Annotated[SourceService, Depends(get_source_service)]
"""Dependency for providing an instance of SourceService."""
