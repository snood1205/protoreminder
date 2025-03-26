from atproto import Client, IdResolver, client_utils, models
from atproto_client.models.app.bsky.feed.post import ReplyRef

from config import ACCOUNT_HANDLE, ACCOUNT_PASSWORD

client = Client()
client.login(ACCOUNT_HANDLE, ACCOUNT_PASSWORD)
account_did = client.me.did

id_resolver = IdResolver()


def post_reply(post, cid, parent_uri, root_uri):
    parent = models.com.atproto.repo.strong_ref.Main(cid=cid, uri=parent_uri)
    root = models.com.atproto.repo.strong_ref.Main(cid=cid, uri=root_uri)
    reply_to = ReplyRef(parent=parent, root=root)
    client.send_post(post, reply_to=reply_to)


def build_mention_post(handle, did, text):
    post = client_utils.TextBuilder()
    post.mention(f"@{handle}", did)
    post.text(text)
    return post


class HandleResolveException(BaseException):
    pass


def resolve_handle(did):
    did_doc = id_resolver.did.resolve(did)
    aka = did_doc.also_known_as
    if not aka or not aka[0]:
        raise HandleResolveException(f"Unable to resolve also-known-as for DID {did}.")
    handle = aka[0].removeprefix("at://")
    if handle == aka[0]:
        raise HandleResolveException(f"Malformed handle URI for DID {did}.")
    return did_doc.also_known_as[0].removeprefix("at://")


class DidResolveException(BaseException):
    pass


def resolve_did(handle):
    did = id_resolver.handle.resolve(handle)
    if not did:
        raise DidResolveException(
            f"Handle {handle} failed to resolve to a DID after 5 attempts."
        )
    return did
