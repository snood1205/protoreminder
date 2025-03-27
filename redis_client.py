from redis import from_url
from config import REDIS_URL
from logging import error
from shutil import get_terminal_size
from subprocess import call, DEVNULL

redis = from_url(REDIS_URL)


def width() -> int:
    try:
        return get_terminal_size().columns
    except OSError:
        return 80


def error_message() -> str:
    banner = "=" * width()
    return "\n" + "\n".join(
        [
            banner,
            "Redis is not running!",
            "Aborting process!",
            "Start redis by running `redis-server`",
            banner,
        ]
    )


def check_redis() -> None:
    if call(["redis-cli", "ping"], stdout=DEVNULL, stderr=DEVNULL) != 0:
        error(error_message())
        exit(1)
