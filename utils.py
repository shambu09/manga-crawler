import logging
import time


def get_logger():
    logger = logging.getLogger("crawler")
    logger.setLevel(logging.INFO)
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)

    fh = logging.FileHandler("crawler.log", mode="a")
    fh.setLevel(logging.INFO)

    formatter = logging.Formatter("%(name)s - %(levelname)s --> %(message)s")
    f_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s --> %(message)s",
        datefmt="%d-%m-%Y %H:%M:%S",
    )

    ch.setFormatter(formatter)
    fh.setFormatter(f_formatter)

    logger.addHandler(ch)
    logger.addHandler(fh)


def timeit(func):
    def wrapper(*args, **kwargs):
        start = time.time()
        tmp = func(*args, **kwargs)
        end = time.time()
        logging.getLogger("crawler.utils.timeit").info(
            f"\"{func.__name__}\" took: {end - start} secs\n")
        return tmp

    return wrapper
