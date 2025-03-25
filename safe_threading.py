from logging import basicConfig, INFO, info, exception
from threading import Event, Thread

shutdown_event = Event()

basicConfig(
    level=INFO, format="%(asctime)s [%(levelname)s] [%(threadName)s] %(message)s"
)


def safe_thread(name, target, **kwargs):
    def wrapped():
        try:
            info(f"{name} started.")
            target(shutdown_event)
        except Exception as e:
            exception(f"{name} crashed with exception: {e}")

    return Thread(target=wrapped, name=name, **kwargs)


def handle_shutdown_signal(signum, _):
    info(f"Received signal {signum}, shutting down...")
    shutdown_event.set()
