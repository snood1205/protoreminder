from at_client import resolve_handle, text_builder_with_mention, post_reply


def handle_no_run_at(did, parent_cid, parent_uri):
    handle = resolve_handle(did)
    post = text_builder_with_mention(
        handle,
        did,
        ", unfortunately I was unable to parse your time. Please try again in a different format (e.g. '50 minutes' or 'January 1, 2040')",
    )
    post_reply(post, parent_cid, parent_uri)


def handle_run_at_in_past(did, parent_cid, parent_uri):
    handle = resolve_handle(did)
    post = text_builder_with_mention(
        handle,
        did,
        ", your reminder time appears to be in the past. I can only handle reminders for the future.",
    )
    post_reply(post, parent_cid, parent_uri)
