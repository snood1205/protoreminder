from datetime import datetime
from json import dumps
from threading import Event
from time import sleep
from typing import Any

from atproto import CAR, AtUri, models
from atproto_client.models.app.bsky.feed.post import ReplyRef
from atproto_client.models.app.bsky.richtext.facet import Mention
from atproto_client.models.com.atproto.sync.subscribe_repos import Commit
from atproto_firehose import FirehoseSubscribeReposClient, parse_subscribe_repos_message
from atproto_firehose.models import MessageFrame

from at_client import AtClient
from date_parse_client import calendar
from error_handler import ErrorHandler
from nlp_client import nlp
from redis_client import redis
from safe_threading import safe_thread


class MentionListener:
    def __init__(self, at_client: AtClient, error_handler: ErrorHandler):
        self.at_client = at_client
        self.error_handler = error_handler

    def parse_create_op(self, commit: Commit) -> tuple[str, AtUri, str, ReplyRef] | None:
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
            if record.facets:
                for facet in record.facets:
                    for feature in facet.features:
                        if (
                            isinstance(feature, Mention)
                            and feature.did == self.at_client.account_did
                        ):
                            return record.text, uri, str(op.cid), record.reply
            reply = getattr(record, "reply", None)
            if reply:
                parent_did = AtUri.from_str(reply.parent.uri).hostname
                if parent_did == self.at_client.account_did:
                    return record.text, uri, str(op.cid), record.reply
        return None

    def enqueue_reminder(
        self, did: str, run_at: datetime, cid: str, parent_uri: str, root_uri: str
    ) -> None:
        handle = self.at_client.resolve_handle(did)
        task = {
            "cid": cid,
            "did": did,
            "handle": handle,
            "parent_uri": parent_uri,
            "root_uri": root_uri,
        }
        redis.zadd("task_queue", {dumps(task): run_at.timestamp()})

    @staticmethod
    def parse_run_at(message: str) -> datetime | None:
        doc = nlp(message)
        for ent in doc.ents:
            if ent.label_ in ("DATE", "TIME"):
                parsed_date_struct, _ = calendar.parse(ent.text)
                return datetime(*parsed_date_struct[:6])
        return None

    def handle_firehose_event(self, message_frame: MessageFrame) -> None:
        commit = parse_subscribe_repos_message(message_frame)
        if not (isinstance(commit, Commit) and commit.blocks):
            return
        result = self.parse_create_op(commit)
        if not result:
            return
        message, uri, cid, reply = result
        parent_uri = (
            reply.parent.uri if reply else f"at://{commit.repo}/app.bsky.feed.post/{uri.rkey}"
        )
        root_uri = reply.root.uri if reply else parent_uri
        run_at = self.parse_run_at(message)
        if not run_at:
            return self.error_handler.handle_no_run_at(commit.repo, cid, parent_uri, root_uri)
        if run_at <= datetime.now():
            return self.error_handler.handle_run_at_in_past(commit.repo, cid, parent_uri, root_uri)
        self.enqueue_reminder(commit.repo, run_at, str(cid), parent_uri, root_uri)

    def run(self, stop_event: Event) -> None:
        client = FirehoseSubscribeReposClient()

        def target(_: Any) -> None:
            client.start(self.handle_firehose_event)

        firehose_thread = safe_thread(target=target, name="FirehoseThread", daemon=True)
        firehose_thread.start()
        try:
            while not stop_event.is_set():
                sleep(0.5)
        finally:
            client.stop()
            firehose_thread.join(timeout=5)
