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
from uuid import uuid4

import pycountry
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.core.database import create_session_factory
from app.core.uow import SQLUnitOfWork
from app.models.country import Country

logger = logging.getLogger(__name__)


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


asyncio.run(init_countries())
