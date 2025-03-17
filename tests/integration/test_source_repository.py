from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.source import Source, SourceHealth, SourceType
from app.repository.source import SourceRepository


@pytest.mark.integration
@pytest.mark.asyncio(loop_scope="session")
async def test_source_repository_basic(db_session: AsyncSession) -> None:

    source_repo = SourceRepository(db_session)

    health = SourceHealth()
    health.id = uuid4()
    health.total_conn_attemps = 100
    health.failed_conn_attemps = 0

    source = Source()
    source.id = uuid4()
    source.name = "a"
    source.uri = "http://127.0.0.1:8080/text.txt"
    source.uri_predefined_type = None
    source.type = SourceType.Text

    await source_repo.add(source)

    stored_source = await source_repo.get_by_id(source.id)
    assert stored_source
    assert stored_source.name == source.name

    stored_source.health = health

    stored_source = await source_repo.update(stored_source)
    assert stored_source.health
    assert stored_source.health.total_conn_attemps == health.total_conn_attemps

    await source_repo.remove(stored_source)

    stored_source = await source_repo.get_by_id(source.id)
    assert stored_source is None
