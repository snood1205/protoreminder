from logging import warning
from at_client import AtClient
from atproto_core.cid import CIDType


class ErrorHandler:
    NO_RUN_MSG = ", unfortunately I was unable to parse your time. Please try again in a different format (e.g. '50 minutes' or 'January 1, 2040')"
    PAST_MSG = ", your reminder time appears to be in the past. I can only handle reminders for the future."

    def __init__(self, at_client: AtClient):
        self.at_client = at_client

    def handle_no_run_at(self, did: str, parent_cid: CIDType, parent_uri):
        warning(f"No run at was parsed for post at URI: {parent_uri}")
        handle = self.at_client.resolve_handle(did)
        post = AtClient.build_mention_post(handle, did, self.NO_RUN_MSG)
        self.at_client.post_reply(post, str(parent_cid), parent_uri)

    def handle_run_at_in_past(self, did, parent_cid, parent_uri):
        warning(f"Run at was parsed to be in the past for post at URI: {parent_uri}")
        handle = self.at_client.resolve_handle(did)
        post = AtClient.build_mention_post(handle, did, self.PAST_MSG)
        self.at_client.post_reply(post, str(parent_cid), parent_uri)
