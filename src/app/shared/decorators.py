import time
from typing import Callable
from app import logger


def retry_on_fail(
    max_retries: int = 3, sleep_interval: float = 0.5, exceptions: tuple = (Exception,)
):
    def wrapper(func: Callable):
        def inner(*args, **kwagrs):
            for i in range(max_retries + 1):
                try:
                    return func(*args, **kwagrs)
                except exceptions as e:
                    if i == max_retries:
                        raise e
                    logger.info(
                        f"Retry: {func.__name__}, {i + 1} times, failed reason: {e}"
                    )
                    logger.info(f"Waiting for {sleep_interval} seconds")
                    time.sleep(sleep_interval)

        return inner

    return wrapper
