from json import loads
from threading import Event
from time import sleep, time
from typing import List, TypedDict, cast

from at_client import AtClient
from redis_client import redis


class Task(TypedDict):
    did: str
    handle: str
    post_cid: str
    post_uri: str


class Scheduler:
    def __init__(self, at_client: AtClient):
        self.at_client = at_client

    def run_task(self, task: Task) -> None:
        handle = task["handle"]
        did = task["did"]
        parent_cid = task["post_cid"]
        parent_uri = task["post_uri"]
        post = AtClient.build_mention_post(handle, did, ", your reminder is ready!")
        self.at_client.post_reply(post, parent_cid, parent_uri)

    def run(self, stop_event: Event) -> None:
        while not stop_event.is_set():
            now = time()
            tasks = cast(List[bytes], redis.zrangebyscore("task_queue", 0, now))
            for raw_task in tasks:
                task: Task = loads(raw_task)
                self.run_task(task)
                redis.zrem("task_queue", raw_task)
            sleep(1)
