import asyncio
import datetime
import logging

from app.core.database import create_session_factory
from app.core.uow import SQLUnitOfWork
from app.models.proxy import Proxy
from app.service.proxy import ProxyService

from .utils.aws_check import check_proxy_with_aws

logger = logging.getLogger(__name__)


async def check_single_proxy(proxy: Proxy) -> Proxy:
    """
    Test a single proxy and updates its health status.

    Increments the attempt count and failure count if the test fails.
    Updates latency and last tested timestamp on success.

    Args:
        proxy (Proxy): The proxy instance to be tested.

    Returns:
        Proxy: The updated proxy instance with new health data.
    """
    success, response_time = await check_proxy_with_aws(
        address=proxy.address,
        port=proxy.port,
        protocol=proxy.protocol,
        login=proxy.login,
        password=proxy.password,
    )

    proxy.health.total_conn_attemps += 1

    if success:
        proxy.health.latency = response_time
        proxy.health.last_tested = datetime.datetime.now(tz=datetime.UTC)
    else:
        proxy.health.failed_conn_attemps += 1

    return proxy


async def check_proxies() -> None:
    """
    Retrieve unchecked proxies from the database, test them, and update their health.

    Proxies are tested concurrently and their updated health data is saved
    back to the database using the ProxyService.
    """
    session_factory = create_session_factory()

    proxy_service = ProxyService(SQLUnitOfWork(session_factory, raise_exc=False))

    proxies = await proxy_service.get_proxies(sort_by_unchecked=True)

    tasks = [check_single_proxy(proxy) for proxy in proxies]

    values = await asyncio.gather(*tasks, return_exceptions=True)

    # filter out exceptions
    checked_proxies = [proxy for proxy in values if not isinstance(proxy, BaseException)]

    # TODO(sny): one single commit
    for proxy in checked_proxies:
        await proxy_service.update(proxy)
