from sqlalchemy import URL
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from .config import database_settings

connection_url = URL.create(
    drivername=database_settings.driver,
    username=database_settings.user,
    password=database_settings.password,
    host=database_settings.host,
    port=database_settings.port,
    database=database_settings.name,
)

async_engine = create_async_engine(connection_url, pool_size=10, max_overflow=2)

async_session_factory = async_sessionmaker(async_engine, expire_on_commit=False)
