from atproto import client_utils
from time import time, sleep
from json import loads

from at_client import client
from redis_client import redis


def run_task(task):
    handle = task["handle"]
    did = task["did"]
    post_url = task["post_url"]

    post = client_utils.TextBuilder()
    post.mention(handle, did)
    post.text(" Your reminder is ready!")
    post.link("Post to remind about", post_url)

    client.send_post(post)


def query_for_and_post_reminders(stop_event):
    while not stop_event.is_set():
        now = time()
        tasks = redis.zrangebyscore("task_queue", 0, now)
        for raw_task in tasks:
            task = loads(raw_task)
            run_task(task)
            redis.zrem("task_queue", raw_task)
        sleep(1)
