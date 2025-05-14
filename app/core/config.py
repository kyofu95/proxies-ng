from typing import Any

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class CommonSettings(BaseSettings):
    """
    Common configuration settings, such as CORS configuration, loaded from environment variables.

    Attributes:
        debug (bool): Enables debug mode when set to True.
        cors_origins (str | None): Comma-separated list of allowed CORS origins.
    """

    debug: bool = Field(alias="DEBUG", default=False)

    cors_origins: str | None = Field(
        alias="CORS_ORIGINS",
        default=None,
        description="If not set, will be set to [*], otherwise 'domain_a,domain_b' will be a list of domains",
    )


common_settings = CommonSettings()


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


class RedisSettings(BaseSettings):
    """
    Configuration settings for Redis, loaded from environment variables.

    Attributes:
        host (str): Redis server hostname or IP address.
        port (int): Redis server port.
        user (str): Redis username, if authentication is required.
        password (str): Redis password, if authentication is required.
    """

    host: str = Field(alias="REDIS_HOST", default="localhost")
    port: int = Field(alias="REDIS_PORT", default=6379)
    user: str = Field(alias="REDIS_USER", default="")
    password: str = Field(alias="REDIS_PASSWORD", default="")


redis_settings = RedisSettings()


class CelerySettings(RedisSettings):
    """
    Configuration settings for Celery broker, optionally using Redis settings as fallback.

    Attributes:
        broker (str): The broker type (e.g., "redis").
        host (str): The broker's hostname or IP address. Defaults to Redis host if not explicitly set.
        port (int): The broker's port number. Defaults to Redis port if not explicitly set.
        user (str): Username for broker authentication. Defaults to Redis user if not explicitly set.
        password (str): Password for broker authentication. Defaults to Redis password if not explicitly set.
        name (str): Broker database name or index (e.g., for Redis).
    """

    broker: str = Field(alias="CELERY_BROKER_DRIVER", default="redis")
    host: str = Field(
        alias="CELERY_BROKER_HOST",
        description="The broker host. Defaults to REDIS_HOST if not explicitly set.",
    )
    port: int = Field(
        alias="CELERY_BROKER_PORT",
        description="The broker port. Defaults to REDIS_PORT if not explicitly set.",
    )
    user: str = Field(
        alias="CELERY_BROKER_USER",
        description="The broker user. Defaults to REDIS_USER if not explicitly set.",
    )
    password: str = Field(
        alias="CELERY_BROKER_PASSWORD",
        description="The broker password. Defaults to REDIS_PASSWORD if not explicitly set.",
    )
    name: str = Field(
        alias="CELERY_BROKER_NAME",
        default="0",
        description="Database name or Redis DB index for the broker",
    )

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @model_validator(mode="before")
    @classmethod
    def fill_from_redis(cls, values: dict[str, Any]) -> dict[str, Any]:
        """
        Fill in missing Celery broker configuration from Redis settings, if available.

        Args:
            values (dict[str, Any]): The initial values from environment variables or defaults.

        Returns:
            dict[str, Any]: The possibly updated values with fallback from Redis settings.
        """
        if "CELERY_BROKER_HOST" not in values:
            redis_host = values.get("REDIS_HOST", redis_settings.host)
            values["CELERY_BROKER_HOST"] = redis_host
        if "CELERY_BROKER_PORT" not in values:
            redis_port = values.get("REDIS_PORT", redis_settings.port)
            values["CELERY_BROKER_PORT"] = redis_port
        if "CELERY_BROKER_USER" not in values:
            redis_user = values.get("REDIS_USER", redis_settings.user)
            values["CELERY_BROKER_USER"] = redis_user
        if "CELERY_BROKER_PASSWORD" not in values:
            redis_password = values.get("REDIS_PASSWORD", redis_settings.password)
            values["CELERY_BROKER_PASSWORD"] = redis_password
        return values


celery_settings = CelerySettings()


class JWTSettings(BaseSettings):
    """
    Configuration settings for JWT encoding and decoding.

    Attributes:
        secret_key (str): The secret key used to sign and verify the JWT.
        algorithm (str): The cryptographic algorithm used for encoding the JWT. Defaults to "HS256".
        access_token_expiry (int): The time in minutes before the access token expires. Defaults to 30 minutes.
    """

    secret_key: str = Field(alias="JWT_SECRET_KEY")
    algorithm: str = "HS256"
    access_token_expiry: int = 30  # 30 minutes

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


jwt_settings = JWTSettings()
