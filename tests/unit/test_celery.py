import pytest

from app.core.config import CelerySettings
from app.tasks.celery import format_broker_url


@pytest.mark.unit
@pytest.mark.asyncio
async def test_format_broker_url_redis_with_auth(monkeypatch: pytest.MonkeyPatch):
    mock_settings = CelerySettings()
    mock_settings.user = "user"
    mock_settings.password = "pass"

    monkeypatch.setattr("app.tasks.celery.celery_settings", mock_settings)

    assert format_broker_url() == "redis://user:pass@localhost:6379/0"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_format_broker_url_redis_without_auth(monkeypatch: pytest.MonkeyPatch):
    mock_settings = CelerySettings()
    mock_settings.broker = "redis"
    mock_settings.user = ""
    mock_settings.password = ""
    mock_settings.host = "localhost"
    mock_settings.port = 6379
    mock_settings.name = "1"

    monkeypatch.setattr("app.tasks.celery.celery_settings", mock_settings)

    assert format_broker_url() == "redis://localhost:6379/1"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_format_broker_url_rabbitmq_with_auth(monkeypatch: pytest.MonkeyPatch):
    mock_settings = CelerySettings()
    mock_settings.broker = "amqp"
    mock_settings.user = "guest"
    mock_settings.password = "guest"
    mock_settings.host = "rabbitmq"
    mock_settings.port = 5672

    monkeypatch.setattr("app.tasks.celery.celery_settings", mock_settings)

    assert format_broker_url() == "amqp://guest:guest@rabbitmq:5672"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_format_broker_url_rabbitmq_without_auth(monkeypatch: pytest.MonkeyPatch):
    mock_settings = CelerySettings()
    mock_settings.broker = "amqp"
    mock_settings.user = ""
    mock_settings.password = ""
    mock_settings.host = "rabbitmq"
    mock_settings.port = 5672

    monkeypatch.setattr("app.tasks.celery.celery_settings", mock_settings)

    assert format_broker_url() == "amqp://rabbitmq:5672"
