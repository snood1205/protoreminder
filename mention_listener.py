from atproto import models, AtUri, CAR
from at_client import account_did, resolve_handle
from atproto_firehose import FirehoseSubscribeReposClient, parse_subscribe_repos_message

from error_handler import handle_no_run_at, handle_run_at_in_past
from safe_threading import safe_thread

from date_parse_client import calendar
from datetime import datetime
from json import dumps
from nlp_client import nlp
from redis_client import redis
from time import sleep

Mention = models.app.bsky.richtext.facet.Mention


def parse_create_op(commit):
    car = CAR.from_bytes(commit.blocks)
    for op in commit.ops:
        if op.action == "create" and op.cid:
            uri = AtUri.from_str(f"at://{commit.repo}/{op.path}")
            if uri.collection == "app.bsky.feed.post":
                blocks = car.blocks.get(op.cid)
                if blocks:
                    record = models.get_or_create(blocks, strict=False)
                    if record.facets:
                        for facet in record.facets:
                            for feature in facet.features:
                                if (
                                    isinstance(feature, Mention)
                                    and feature.did == account_did
                                ):
                                    return record.text, uri, op.cid


def enqueue_reminder(did, run_at, post_cid, post_uri):
    handle = resolve_handle(did)
    task = {"did": did, "handle": handle, "post_cid": post_cid, "post_uri": post_uri}
    redis.zadd("task_queue", {dumps(task): run_at.timestamp()})


def parse_run_at(message):
    doc = nlp(message)
    for ent in doc.ents:
        if ent.label_ in ("DATE", "TIME"):
            parsed_date_struct, _ = calendar.parse(ent.text)
            return datetime(*parsed_date_struct[:6])


def handle_firehose_event(message_frame):
    commit = parse_subscribe_repos_message(message_frame)
    if not (
        isinstance(commit, models.ComAtprotoSyncSubscribeRepos.Commit) and commit.blocks
    ):
        return
    result = parse_create_op(commit)
    if not result:
        return
    message, uri, cid = result
    run_at = parse_run_at(message)
    if not run_at:
        return handle_no_run_at(commit.repo)
    if run_at <= datetime.now():
        return handle_run_at_in_past(commit.repo)

    post_uri = f"at://{commit.repo}/app.bsky.feed.post/{uri.rkey}"
    enqueue_reminder(commit.repo, run_at, str(cid), post_uri)


def listen_for_mentions(stop_event):
    client = FirehoseSubscribeReposClient()

    def run(_):
        client.start(handle_firehose_event)

    firehose_thread = safe_thread(target=run, name="FirehoseThread", daemon=True)
    firehose_thread.start()

    try:
        while not stop_event.is_set():
            sleep(0.5)
    finally:
        client.stop()
        firehose_thread.join(timeout=5)
