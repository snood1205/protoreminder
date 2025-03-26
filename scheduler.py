from time import time, sleep
from json import loads

from at_client import build_mention_post, post_reply
from redis_client import redis


def run_task(task):
    handle = task["handle"]
    did = task["did"]
    parent_cid = task["post_cid"]
    parent_uri = task["post_uri"]

    post = build_mention_post(handle, did, ", your reminder is ready!")
    post_reply(post, parent_cid, parent_uri)


def query_for_and_post_reminders(stop_event):
    while not stop_event.is_set():
        now = time()
        tasks = redis.zrangebyscore("task_queue", 0, now)
        for raw_task in tasks:
            task = loads(raw_task)
            run_task(task)
            redis.zrem("task_queue", raw_task)
        sleep(1)
