from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
import pytest_asyncio

from app.core.uow import SQLUnitOfWork
from app.models.source import Source, SourceType
from app.service.source import SourceService

@pytest_asyncio.fixture(loop_scope="module", scope="module")
async def mock_uow() -> AsyncMock:
    uow = AsyncMock(SQLUnitOfWork)
    uow.__aenter__.return_value = uow
    uow.proxy_repository = AsyncMock()
    uow.source_repository = AsyncMock()
    return uow


@pytest_asyncio.fixture(loop_scope="module", scope="module")
async def service(mock_uow: AsyncMock) -> SourceService:
    return SourceService(mock_uow)


@pytest.mark.asyncio
async def test_create_source(service: SourceService, mock_uow: AsyncMock) -> None:
    source_id = uuid4()
    name = "Test Source"
    uri_type = None

    mock_source = Source()
    mock_source.id = source_id
    mock_source.name = name
    mock_source.uri_predefined_type = uri_type
    mock_source.type = SourceType.Text

    mock_uow.source_repository.add.return_value = mock_source
    result = await service.create(name)
    
    mock_uow.source_repository.add.assert_called_once()
    assert result == mock_source


@pytest.mark.asyncio
async def test_get_by_id(service: SourceService, mock_uow: AsyncMock) -> None:
    source_id = uuid4()
    mock_source = Source()
    mock_source.id = source_id

    mock_uow.source_repository.get_by_id.return_value = mock_source
    result = await service.get_by_id(source_id)
    
    mock_uow.source_repository.get_by_id.assert_called_once_with(source_id)
    assert result == mock_source


@pytest.mark.asyncio
async def test_update_source(service: SourceService, mock_uow: AsyncMock) -> None:
    mock_source = Source()
    mock_uow.source_repository.update.return_value = mock_source

    result = await service.update(mock_source)
    
    mock_uow.source_repository.update.assert_called_once_with(mock_source)
    assert result == mock_source


@pytest.mark.asyncio
async def test_remove_source(service: SourceService, mock_uow: AsyncMock) -> None:
    mock_source = Source()

    await service.remove(mock_source)
    
    mock_uow.source_repository.remove.assert_called_once_with(mock_source)
