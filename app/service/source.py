from uuid import UUID, uuid4

from app.core.exceptions import AlreadyExistsError
from app.core.uow import SQLUnitOfWork
from app.models.proxy import Protocol
from app.models.source import Source, SourceHealth, SourceType


class SourceService:
    """
    Service class for handling operations related to proxy sources.

    This class provides methods for creating, retrieving, updating,
    and deleting proxy sources using the repository pattern.
    """

    def __init__(self, uow: SQLUnitOfWork) -> None:
        """
        Initialize the SourceService with an asynchronous database session.

        Args:
            uow (SQLUnitOfWork): The unit-of-work instance.
        """
        self.uow = uow

    async def create(self, name: str, url: str, uri_type: Protocol | None = None) -> Source:
        """
        Create a new proxy source with the given parameters and store it in database.

        If a proxy source with the same name already exists, raises an 'AlreadyExistsError'.

        Args:
            name (str): The name of the proxy source.
            url (str): The URL associated with the proxy source.
            uri_type (Protocol | None): Optional URI type (proxy protocol) for the source. Defaults to None.

        Raises:
            AlreadyExistsError: If a source with the same name already exists.

        Returns:
            Source: The newly created proxy source object.
        """
        existing_source = await self.get_by_name(name)
        if existing_source:
            raise AlreadyExistsError("Source with such name already exists")

        source = Source()
        source.id = uuid4()
        source.name = name
        source.uri = url
        source.uri_predefined_type = uri_type
        source.type = SourceType.Text

        source_health = SourceHealth()
        source_health.id = uuid4()
        source_health.total_conn_attemps = 0
        source_health.failed_conn_attemps = 0

        source.health = source_health

        async with self.uow as uow:
            return await uow.source_repository.add(source)

    async def get_by_id(self, id_: UUID) -> Source | None:
        """
        Retrieve a proxy source by its unique ID.

        Args:
            id_ (UUID): The unique identifier of the proxy source.

        Returns:
            Source | None: The proxy source object if found, otherwise None.
        """
        async with self.uow as uow:
            return await uow.source_repository.get_by_id(id_)

    async def get_by_name(self, name: str) -> Source | None:
        """
        Retrieve a proxy source by its name.

        Args:
            name (str): The name of the proxy source.

        Returns:
            Source | None: The proxy source object if found, otherwise None.
        """
        async with self.uow as uow:
            return await uow.source_repository.get_by_name(name)

    async def update(self, source: Source) -> Source:
        """
        Update an existing proxy source in the database.

        Args:
            source (Source): The proxy source object with updated data.

        Returns:
            Source: The updated proxy source object.
        """
        async with self.uow as uow:
            return await uow.source_repository.update(source)

    async def remove(self, source: Source) -> None:
        """
        Remove a proxy source from the database.

        Args:
            source (Source): The proxy source object to be removed.
        """
        async with self.uow as uow:
            await uow.source_repository.remove(source)

    async def get_sources(self) -> list[Source]:
        """
        Retrieve all available proxy sources from the database.

        Returns:
            list[Source]: A list of all proxy source objects.
        """
        async with self.uow as uow:
            return await uow.source_repository.get_sources()
