from mention_listener import listen_for_mentions
from scheduler import query_for_and_post_reminders
from signal import signal, SIGINT, SIGTERM

from safe_threading import handle_shutdown_signal, safe_thread, shutdown_event


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
