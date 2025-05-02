import asyncio

import pytest

from app.tasks.utils.gather import cgather


@pytest.mark.asyncio
async def test_cgather_filters_none_and_exceptions():
    async def return_value(val):
        await asyncio.sleep(0.01)
        return val

    async def return_none():
        await asyncio.sleep(0.01)
        return None

    async def raise_error():
        await asyncio.sleep(0.01)
        raise ValueError("Something went wrong")

    tasks = [
        return_value(1),
        return_value(2),
        return_none(),
        raise_error(),
        return_value(3),
    ]

    result = await cgather(*tasks, limit=2)

    # Only values 1, 2, 3 should remain
    assert sorted(result) == [1, 2, 3]


@pytest.mark.asyncio
async def test_cgather_respects_concurrency_limit():
    running = 0
    max_running = 0

    async def task(val):
        nonlocal running, max_running
        running += 1
        max_running = max(max_running, running)
        await asyncio.sleep(0.01)
        running -= 1
        return val

    tasks = [task(i) for i in range(10)]

    result = await cgather(*tasks, limit=3)

    assert sorted(result) == list(range(10))
    assert max_running <= 3
