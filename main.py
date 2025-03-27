from at_client import AtClient
from error_handler import ErrorHandler
from mention_listener import MentionListener
from redis_client import check_redis
from safe_threading import handle_shutdown_signal, safe_thread
from scheduler import Scheduler
from signal import signal, SIGINT, SIGTERM


def main():
    check_redis()
    signal(SIGINT, handle_shutdown_signal)
    signal(SIGTERM, handle_shutdown_signal)
    at_client = AtClient()
    error_handler = ErrorHandler(at_client=at_client)
    scheduler = Scheduler(at_client=at_client)
    listener = MentionListener(at_client=at_client, error_handler=error_handler)
    listener_thread = safe_thread(name="MentionListener", target=listener.run)
    scheduler_thread = safe_thread(name="ReminderScheduler", target=scheduler.run)
    listener_thread.start()
    scheduler_thread.start()
    listener_thread.join()
    scheduler_thread.join()


if __name__ == "__main__":
    main()
