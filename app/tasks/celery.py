from celery import Celery

from app.core.config import celery_settings


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

celery_app.conf.update(
    task_serializer="json",
    result_backend=celery_broker,
)


@celery_app.task
def get_proxy_sources_task() -> None:
    """Celery basic task to retrieve proxy sources."""


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
