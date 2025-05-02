import asyncio
from collections.abc import Awaitable
from typing import TypeVar

T = TypeVar("T")


async def cgather(*tasks: Awaitable[T | None], limit: int = 50) -> list[T]:
    """
    Asynchronously gather results with a concurrency limit.

    This function allows running multiple asynchronous tasks concurrently, but limits the number of tasks
    running at the same time based on the provided 'limit'. It filters out 'None' values and exceptions from
    the results before returning.

    Args:
        *tasks (Awaitable[T | None]): The asynchronous tasks to run. Each task is expected
            to return a value of type 'T' or 'None'.
        limit (int, optional): The maximum number of tasks to run concurrently. Default is 50.

    Returns:
        list[T]: A list of results from the tasks, excluding any `None` values and exceptions.
    """
    semaphore = asyncio.Semaphore(limit)

    async def sem_task(task: Awaitable[T | None]) -> T | None:
        async with semaphore:
            return await task

    results = await asyncio.gather(
        *[sem_task(task) for task in tasks],
        return_exceptions=True,
    )

    # filter out exceptions
    return [value for value in results if value is not None and not isinstance(value, BaseException)]
