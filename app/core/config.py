from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseSettings(BaseSettings):
    """
    Configuration settings for the database, loaded from environment variables.

    Attributes:
        driver (str): The database driver (e.g., 'postgresql', 'mysql').
        user (str): The username for database authentication.
        password (str): The password for database authentication.
        name (str): The name of the database.
        host (str): The database server's hostname or IP address.
        port (int): The port number on which the database server is listening.
    """

    driver: str = Field(alias="DATABASE_DRIVER", default="postgresql+asyncpg")
    user: str = Field(alias="DATABASE_USER", default="myuser")
    password: str = Field(alias="DATABASE_PASSWORD", default="mypassword")
    name: str = Field(alias="DATABASE_NAME", default="mydb")
    host: str = Field(alias="DATABASE_HOST", default="localhost")
    port: int = Field(alias="DATABASE_PORT", default=5432)

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


database_settings = DatabaseSettings()


class CelerySettings(BaseSettings):
    """
    Configuration settings for Celery broker connection.

    Attributes:
        broker (str): The message broker type (e.g., "redis", "rabbitmq"). Defaults to "redis".
        user (str): The username for broker authentication. Defaults to an empty string.
        password (str): The password for broker authentication. Defaults to an empty string.
        host (str): The hostname or IP address of the broker. Defaults to "localhost".
        port (int): The port number of the broker. Defaults to 6379.
        name (str): The database name for the broker (if applicable). Defaults to "0".
    """

    broker: str = Field(alias="CELERY_BROKER_DRIVER", default="redis")
    user: str = Field(alias="CELERY_BROKER_USER", default="")
    password: str = Field(alias="CELERY_BROKER_PASSWORD", default="")
    host: str = Field(alias="CELERY_BROKER_HOST", default="localhost")
    port: int = Field(alias="CELERY_BROKER_PORT", default=6379)
    name: str = Field(alias="CELERY_BROKER_NAME", default="0", description="database name")

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


celery_settings = CelerySettings()
