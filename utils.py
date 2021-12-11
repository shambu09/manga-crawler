import asyncio
import logging
import time


def get_logger():
    logger = logging.getLogger("crawler")
    logger.setLevel(logging.DEBUG)

    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)

    fh = logging.FileHandler("logs/crawler.log", mode="a")
    fh.setLevel(logging.INFO)

    fh2 = logging.FileHandler("logs/crawler-error.log", mode="a")
    fh2.setLevel(logging.ERROR)

    fh3 = logging.FileHandler("logs/crawler-debug.log", mode="a")
    fh3.setLevel(logging.DEBUG)

    formatter = logging.Formatter("%(name)s - %(levelname)s --> %(message)s")
    f_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s --> %(message)s",
        datefmt="%d-%m-%Y %H:%M:%S",
    )

    ch.setFormatter(formatter)
    fh.setFormatter(f_formatter)
    fh2.setFormatter(f_formatter)
    fh3.setFormatter(f_formatter)

    logger.addHandler(ch)
    logger.addHandler(fh)
    logger.addHandler(fh2)
    logger.addHandler(fh3)


def timeit(func):
    def wrapper(*args, **kwargs):
        start = time.time()
        tmp = func(*args, **kwargs)
        end = time.time()
        logging.getLogger("crawler.utils.timeit").debug(
            f"\"{func.__name__}\" took: {end - start} secs\n")
        return tmp

    return wrapper


def retry(method, max_retries=5, delay=0):
    def decorator(func):
        def wrapper(*args, _type="", **kwargs):
            limit = {"retries": max_retries + 1, "delay": delay, "count": -1}
            if _type == "":
                _type = method

            resp = None
            while limit["retries"] > 0:
                try:
                    resp = func(*args, **kwargs)

                except Exception as e:
                    logging.getLogger("crawler.utils.retry").warning(
                        f"{_type}: {func.__name__} failed with: {e}")

                    limit["retries"] -= 1
                    limit["count"] += 1
                    limit["delay"] = limit["delay"] * 2

                    if limit["retries"] > 0:
                        logging.getLogger("crawler.utils.retry").warning(
                            f"{_type}: Retrying {func.__name__} (retry: #{limit['count']})"
                        )

                        if limit['delay'] > 0:
                            time.sleep(limit["delay"])

                    else:
                        logging.getLogger("crawler.utils.retry").error(
                            f"{_type}: {func.__name__} failed after {max_retries} retries --> {e}"
                        )
                        return resp
                else:
                    if limit["count"] != -1:
                        logging.getLogger("crawler.utils.retry").info(
                            f"{_type}: {func.__name__} retry succeeded (retry: #{limit['count']})"
                        )
                    return resp
            return resp

        return wrapper

    return decorator


def retry_async(method, max_retries=5, delay=0):
    def decorator(func):
        async def wrapper(*args, _type="", **kwargs):
            limit = {"retries": max_retries + 1, "delay": delay, "count": -1}
            if _type == "":
                _type = method

            error = None
            resp = None
            while limit["retries"] > 0:
                try:
                    resp = await func(*args, **kwargs)

                except asyncio.TimeoutError as e:
                    logging.getLogger("crawler.utils.retry").warning(
                        f"{_type}: {func.__name__} failed with: Timeout error")
                    error = "Timeout error"

                except Exception as e:
                    logging.getLogger("crawler.utils.retry").warning(
                        f"{_type}: {func.__name__} failed with: {e}")
                    error = e

                else:
                    if limit["count"] != -1:
                        logging.getLogger("crawler.utils.retry").info(
                            f"{_type}: {func.__name__} retry succeeded (retry: #{limit['count']})"
                        )
                    return resp

                limit["retries"] -= 1
                limit["count"] += 1
                limit["delay"] = limit["delay"] * 2

                if limit["retries"] > 0:
                    logging.getLogger("crawler.utils.retry").warning(
                        f"{_type}: Retrying {func.__name__} (retry: #{limit['count']})"
                    )

                    if limit['delay'] > 0:
                        await asyncio.sleep(limit["delay"])

                else:
                    logging.getLogger("crawler.utils.retry").error(
                        f"{_type}: {func.__name__} failed after {max_retries} retries --> {error}"
                    )
                    return resp
            return resp

        return wrapper

    return decorator
