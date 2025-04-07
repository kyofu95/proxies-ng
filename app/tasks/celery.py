import asyncio
from collections.abc import Callable, Coroutine
from typing import Any

from celery import Celery, current_task
from redis.asyncio import ConnectionPool, Redis

from app.core.config import celery_settings, redis_settings

from .fetch_proxies import fetch_proxies


def format_broker_url() -> str:
    """
    Format the broker URL for Celery.

    Returns:
        str: The formatted broker URL.
    """
    credentials = ""
    if celery_settings.password:
        credentials = f"{celery_settings.user if celery_settings.user else ''}:{celery_settings.password}@"
    url = f"{celery_settings.broker}://{credentials}{celery_settings.host}:{celery_settings.port}"
    if celery_settings.broker.lower() == "redis":
        url = url + f"/{celery_settings.name}"
    return url.lower()


celery_broker = format_broker_url()

celery_app = Celery("tasks", broker=celery_broker, backend=celery_broker)


def get_redis() -> Redis:
    """
    Create and return a Redis client using the configured Redis settings.

    Returns:
        Redis: An asyncio-compatible Redis client.
    """
    pool = ConnectionPool.from_url(f"redis://{redis_settings.host}:{redis_settings.port}/1")
    return Redis(connection_pool=pool, decode_responses=True)


celery_app.conf.update(
    task_serializer="json",
    result_backend=celery_broker,
)

type Coro = Callable[[], Coroutine[Any, Any, None]]


async def async_task_runner(func: Coro) -> None:
    """
    Run an async task with Redis-based locking to prevent concurrent execution.

    This function ensures that only one instance of the given task is running at a time.
    It uses Redis to acquire a lock and clears it once the task is done.

    Args:
        func (Coro): The coroutine function to run.

    Raises:
        ValueError: If the Celery task does not have an associated ID.
    """
    redis_key = f"lock:{func.__name__}"
    task_id = current_task.request.id
    if not task_id:
        raise ValueError("No task id provided")

    redis = get_redis()
    if not await redis.set(redis_key, task_id, ex=300, nx=True):
        # task already running
        return

    try:
        await func()
    finally:
        current_value = await redis.get(redis_key)
        if current_value == task_id:
            await redis.delete(redis_key)


@celery_app.task
def get_proxy_sources_task() -> None:
    """Celery basic task to retrieve proxy sources."""
    asyncio.run(async_task_runner(fetch_proxies))


@celery_app.task
def check_proxies_task() -> None:
    """Celery basic task to check proxies availability and validity."""


celery_app.autodiscover_tasks()

celery_app.conf.beat_schedule = {
    "task_a_every_6_hours": {
        "task": "tasks.get_proxy_sources_task",
        "schedule": 6 * 60 * 60,  # 6 hours
        "options": {"queue": "default"},
    },
    "task_b_every_20_minutes": {
        "task": "tasks.check_proxies_task",
        "schedule": 20 * 60,  # 20 minutes
        "options": {"queue": "default"},
    },
}

celery_app.conf.timezone = "UTC"
