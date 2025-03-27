from logging import INFO, basicConfig, exception, info
from threading import Event, Thread
from typing import Any, Callable, TypedDict, Unpack

shutdown_event = Event()

basicConfig(level=INFO, format="%(asctime)s [%(levelname)s] [%(threadName)s] %(message)s")


class Kwargs(TypedDict, total=False):
    daemon: bool


def safe_thread(name: str, target: Callable[[Event], None], **kwargs: Unpack[Kwargs]) -> Thread:
    def wrapped() -> None:
        try:
            info(f"{name} started.")
            target(shutdown_event)
        except Exception as e:
            exception(f"{name} crashed with exception: {e}")

    return Thread(target=wrapped, name=name, **kwargs)


def handle_shutdown_signal(signum: int, _: Any) -> None:
    info(f"Received signal {signum}, shutting down...")
    shutdown_event.set()
