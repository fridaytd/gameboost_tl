import logging
from typing import Callable

from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_fixed,
    before_sleep_log,
)

_logger = logging.getLogger(__name__)


def retry_on_fail(
    max_retries: int = 3, sleep_interval: float = 0.5, exceptions: tuple = (Exception,)
) -> Callable:
    def wrapper(func: Callable) -> Callable:
        return retry(
            stop=stop_after_attempt(max_retries + 1),
            wait=wait_fixed(sleep_interval),
            retry=retry_if_exception_type(exceptions),
            before_sleep=before_sleep_log(_logger, logging.INFO),
            reraise=True,
        )(func)

    return wrapper
