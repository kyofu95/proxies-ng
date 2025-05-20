"""
Initialize country lookup table before running the server.

This module populates the 'countries' table in the database with entries
from the ISO 3166-1 alpha-2 standard using the `pycountry` library. It is meant
to be run manually or as part of a setup script before starting the server,
ensuring that all supported countries are available for geolocation
and proxy metadata resolution.
"""

import asyncio
import logging
import os
import sys
from uuid import uuid4

import pycountry
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.core.database import create_session_factory
from app.core.uow import SQLUnitOfWork
from app.models.country import Country
from app.service.user import UserService

logger = logging.getLogger(__name__)

# output info to stdout
console = logging.StreamHandler(sys.stdout)
logger.addHandler(console)


async def init_countries() -> None:
    """
    Insert countries into the database if they do not already exist.

    Uses the pycountry library to retrieve all ISO 3166 countries
    and inserts them using ON CONFLICT DO NOTHING to avoid duplicates.

    Returns:
        None
    """
    logger.info("Initializing database lookup tables")
    session_factory = create_session_factory()
    async with SQLUnitOfWork(session_factory, raise_exc=False) as uow:
        countries = []
        for country in pycountry.countries:
            countries.append(  # noqa: PERF401
                {
                    "id": uuid4(),
                    "code": country.alpha_2,
                    "name": country.name,
                },
            )
        stmt = pg_insert(Country).values(countries).on_conflict_do_nothing()
        if uow.session:
            await uow.session.execute(stmt)
        else:
            logger.debug("UoW seesion is not initialized")


async def init_admin() -> None:
    """
    Create an admin user if it does not already exist.

    The login and password are read from the environment variables ADMIN_LOGIN and ADMIN_PASSWORD.
    """
    logger.info("Creating admin")

    session_factory = create_session_factory()
    user_service = UserService(SQLUnitOfWork(session_factory, raise_exc=False))

    login = os.getenv("ADMIN_LOGIN", "admin")
    password = os.getenv("ADMIN_PASSWORD", "password")

    admin = await user_service.get_by_login(login)
    if not admin:
        admin = await user_service.create(login, password)
    else:
        logger.info("Admin already exist")


asyncio.run(init_countries())
