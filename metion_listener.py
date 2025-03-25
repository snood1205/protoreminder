from atproto import models, AtUri, CAR
from atproto_firehose import FirehoseSubscribeReposClient, parse_subscribe_repos_message
from atproto_client import did
from nlp_client import nlp
from date_parse_client import calendar
from datetime import datetime


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
                                    type(feature)
                                    is models.app.bsky.richtext.facet.Mention
                                ):
                                    if feature.did == did:
                                        return record.text


def enqueue_reminder(handle, message_url, run_at):
    pass


def parse_run_at(message):
    doc = nlp(message)
    for ent in doc.ents:
        if ent.label_ in ("DATE", "TIME"):
            parsed_date_struct, _ = calendar.parse(ent.text)
            return datetime(*parsed_date_struct[:6])


def handle_firehose_event(message_frame):
    commit = parse_subscribe_repos_message(message_frame)
    if (
        not isinstance(commit, models.ComAtprotoSyncSubscribeRepos.Commit)
        or not commit.blocks
    ):
        return
    message = parse_create_op(commit)
    run_at = parse_run_at(message)
    enqueue_reminder(commit.author, commit.url, run_at)


def listen_for_mentions():
    client = FirehoseSubscribeReposClient()
    client.start(handle_firehose_event)
