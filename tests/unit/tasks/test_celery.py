from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.config import CelerySettings
from app.tasks.celery import async_task_runner, format_broker_url


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


@pytest.mark.unit
@pytest.mark.asyncio
async def test_async_task_runner_runs_once_and_unlocks():
    mock_coro_func = AsyncMock()
    mock_coro_func.__name__ = "mock_task"

    fake_task_id = "abc123"

    with (
        patch("app.tasks.celery.get_redis") as mock_get_redis,
        patch("app.tasks.celery.current_task") as mock_current_task,
    ):
        mock_redis = AsyncMock()
        mock_redis.set.return_value = True
        mock_redis.get.return_value = fake_task_id
        mock_get_redis.return_value = mock_redis

        mock_current_task.request.id = fake_task_id

        await async_task_runner(mock_coro_func)

        mock_coro_func.assert_awaited_once()
        mock_redis.set.assert_awaited_once_with("lock:mock_task", fake_task_id, ex=300, nx=True)
        mock_redis.delete.assert_awaited_once_with("lock:mock_task")


@pytest.mark.unit
@pytest.mark.asyncio
async def test_async_task_runner_skips_if_lock_exists():
    mock_coro_func = AsyncMock()
    mock_coro_func.__name__ = "locked_task"

    with (
        patch("app.tasks.celery.get_redis") as mock_get_redis,
        patch("app.tasks.celery.current_task") as mock_current_task,
    ):
        mock_redis = AsyncMock()
        mock_redis.set.return_value = False  # lock already exists
        mock_get_redis.return_value = mock_redis

        mock_current_task.request.id = "some_id"

        await async_task_runner(mock_coro_func)

        mock_coro_func.assert_not_called()
        mock_redis.delete.assert_not_called()


@pytest.mark.unit
@pytest.mark.asyncio
async def test_async_task_runner_raises_without_task_id():
    mock_func = AsyncMock()
    mock_func.__name__ = "no_id_task"

    with patch("app.tasks.celery.current_task") as mock_current_task:
        mock_current_task.request.id = None
        with pytest.raises(ValueError, match="No task id provided"):
            await async_task_runner(mock_func)
