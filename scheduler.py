from atproto import client_utils, models
from time import time, sleep
from json import loads

from atproto_client.models.app.bsky.feed.post import ReplyRef

from at_client import client
from redis_client import redis


def run_task(task):
    handle = task["handle"]
    did = task["did"]
    cid = task["post_cid"]
    uri = task["post_uri"]
    parent = models.com.atproto.repo.strong_ref.Main(cid=cid, uri=uri)
    reply_to = ReplyRef(parent=parent,root=parent)

    post = client_utils.TextBuilder()
    post.mention(f"@{handle}", did)
    post.text(", your reminder is ready!")

    print(f"Handle:\t{handle}\nDID:\t{did}")
    print(f"URI:\t{uri}\nCID:\t{cid}")
    client.send_post(post, reply_to=reply_to)


def query_for_and_post_reminders(stop_event):
    while not stop_event.is_set():
        now = time()
        tasks = redis.zrangebyscore("task_queue", 0, now)
        for raw_task in tasks:
            task = loads(raw_task)
            run_task(task)
            redis.zrem("task_queue", raw_task)
        sleep(1)
