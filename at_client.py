from atproto import Client, IdResolver, client_utils, models
from atproto_client.models.app.bsky.feed.post import ReplyRef
from atproto_client.models.com.atproto.repo.strong_ref import Main
from config import ACCOUNT_HANDLE, ACCOUNT_PASSWORD


class AtClient:
    def __init__(self):
        self.client = Client()
        self.client.login(ACCOUNT_HANDLE, ACCOUNT_PASSWORD)
        self.account_did = self.client.me.did
        self.id_resolver = IdResolver()

    def post_reply(self, post: client_utils.TextBuilder, parent_cid: str, parent_uri: str) -> None:
        parent = Main(cid=parent_cid, uri=parent_uri)
        reply_to = ReplyRef(parent=parent, root=parent)
        self.client.send_post(post, reply_to=reply_to)

    @staticmethod
    def build_mention_post(handle: str, did: str, text: str) -> client_utils.TextBuilder:
        post = client_utils.TextBuilder()
        post.mention(f"@{handle}", did)
        post.text(text)
        return post

    def resolve_handle(self, did: str) -> str:
        did_doc = self.id_resolver.did.resolve(did)
        aka = did_doc.also_known_as
        if not aka or not aka[0]:
            raise HandleResolveException(f"Unable to resolve also-known-as for DID {did}.")
        handle = aka[0].removeprefix("at://")
        if handle == aka[0]:
            raise HandleResolveException(f"Malformed handle URI for DID {did}.")
        return did_doc.also_known_as[0].removeprefix("at://")

    def resolve_did(self, handle: str) -> str:
        did = self.id_resolver.handle.resolve(handle)
        if not did:
            raise DidResolveException(f"@{handle} failed to resolve to a DID.")
        return did


class DidResolveException(BaseException):
    pass


class HandleResolveException(BaseException):
    pass
