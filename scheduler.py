from atproto import client_utils
from time import time, sleep
from json import loads

from atproto_client import client, id_resolver
from redis_client import redis


def run_task(task):
    handle = task["handle"]
    did = id_resolver.handle.resolve(handle)

    post = client_utils.TextBuilder()
    post.mention(handle, did)
    post.text(" Your reminder is ready!")

    client.send_post(post)


def query_for_and_post_reminders():
    while True:
        now = time()
        tasks = redis.zrangebyscore("task_queue", 0, now)
        for raw_task in tasks:
            task = loads(raw_task)
            run_task(task)
        sleep(1)
