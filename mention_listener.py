from atproto import models, AtUri, CAR
from at_client import AtClient
from atproto_firehose import FirehoseSubscribeReposClient, parse_subscribe_repos_message
from error_handler import ErrorHandler
from safe_threading import safe_thread
from date_parse_client import calendar
from datetime import datetime
from json import dumps
from nlp_client import nlp
from redis_client import redis
from time import sleep

Mention = models.app.bsky.richtext.facet.Mention


class MentionListener:
    def __init__(self, at_client: AtClient, error_handler: ErrorHandler):
        self.at_client = at_client
        self.error_handler = error_handler

    def parse_create_op(self, commit):
        car = CAR.from_bytes(commit.blocks)
        for op in commit.ops:
            if op.action != "create" or not op.cid:
                continue
            uri = AtUri.from_str(f"at://{commit.repo}/{op.path}")
            if uri.collection != "app.bsky.feed.post":
                continue
            blocks = car.blocks.get(op.cid)
            if not blocks:
                continue
            record = models.get_or_create(blocks, strict=False)
            if not record.facets:
                continue
            for facet in record.facets:
                for feature in facet.features:
                    if (
                        isinstance(feature, Mention)
                        and feature.did == self.at_client.account_did
                    ):
                        return record.text, uri, op.cid

    def enqueue_reminder(self, did, run_at, post_cid, post_uri):
        handle = self.at_client.resolve_handle(did)
        task = {
            "did": did,
            "handle": handle,
            "post_cid": post_cid,
            "post_uri": post_uri,
        }
        redis.zadd("task_queue", {dumps(task): run_at.timestamp()})

    @staticmethod
    def parse_run_at(message):
        doc = nlp(message)
        for ent in doc.ents:
            if ent.label_ in ("DATE", "TIME"):
                parsed_date_struct, _ = calendar.parse(ent.text)
                return datetime(*parsed_date_struct[:6])

    def handle_firehose_event(self, message_frame):
        commit = parse_subscribe_repos_message(message_frame)
        if not (
            isinstance(commit, models.ComAtprotoSyncSubscribeRepos.Commit)
            and commit.blocks
        ):
            return
        result = self.parse_create_op(commit)
        if not result:
            return
        message, uri, cid = result
        post_uri = f"at://{commit.repo}/app.bsky.feed.post/{uri.rkey}"
        run_at = self.parse_run_at(message)
        if not run_at:
            return self.error_handler.handle_no_run_at(commit.repo, cid, post_uri)
        if run_at <= datetime.now():
            return self.error_handler.handle_run_at_in_past(commit.repo, cid, post_uri)
        self.enqueue_reminder(commit.repo, run_at, str(cid), post_uri)

    def run(self, stop_event):
        client = FirehoseSubscribeReposClient()

        def run(_):
            client.start(self.handle_firehose_event)

        firehose_thread = safe_thread(target=run, name="FirehoseThread", daemon=True)
        firehose_thread.start()
        try:
            while not stop_event.is_set():
                sleep(0.5)
        finally:
            client.stop()
            firehose_thread.join(timeout=5)
