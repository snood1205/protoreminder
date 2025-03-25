from logging import basicConfig, INFO, info, exception
from mention_listener import listen_for_mentions
from scheduler import query_for_and_post_reminders
from threading import Event, Thread
from signal import signal, SIGINT, SIGTERM

basicConfig(
    level=INFO, format="%(asctime)s [%(levelname)s] [%(threadName)s] %(message)s"
)

shutdown_event = Event()


def safe_thread(name, target):
    def wrapped():
        try:
            info(f"{name} started.")
            target(shutdown_event)
        except Exception as e:
            exception(f"{name} crashed with exception: {e}")

    return Thread(target=wrapped, name=name)


def handle_shutdown_signal(signum, _):
    info(f"Received signal {signum}, shutting down...")
    shutdown_event.set()


def main():
    signal(SIGINT, handle_shutdown_signal)
    signal(SIGTERM, handle_shutdown_signal)
    listener_thread = safe_thread(name="MentionListener", target=listen_for_mentions)
    scheduler_thread = safe_thread(
        name="ReminderScheduler", target=query_for_and_post_reminders
    )
    listener_thread.start()
    scheduler_thread.start()
    listener_thread.join()
    scheduler_thread.join()


if __name__ == "__main__":
    main()
