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

    driver: str = Field(alias="DATABASE_DRIVER")
    user: str = Field(alias="DATABASE_USER")
    password: str = Field(alias="DATABASE_PASSWORD")
    name: str = Field(alias="DATABASE_NAME")
    host: str = Field(alias="DATABASE_HOST")
    port: int = Field(alias="DATABASE_PORT")

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


database_settings = DatabaseSettings()
