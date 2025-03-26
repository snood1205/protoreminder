from logging import warning

from at_client import resolve_handle, build_mention_post, post_reply


def handle_no_run_at(did, parent_cid, parent_uri):
    warning(f"No run at was parsed for post at URI: {parent_uri}")
    handle = resolve_handle(did)
    post = build_mention_post(
        handle,
        did,
        ", unfortunately I was unable to parse your time. Please try again in a different format (e.g. '50 minutes' or 'January 1, 2040')",
    )
    post_reply(post, parent_cid, parent_uri)


def handle_run_at_in_past(did, parent_cid, parent_uri):
    warning(f"Run at was parsed to be in the past for post at URI: {parent_uri}")
    handle = resolve_handle(did)
    post = build_mention_post(
        handle,
        did,
        ", your reminder time appears to be in the past. I can only handle reminders for the future.",
    )
    post_reply(post, parent_cid, parent_uri)
