from atproto import Client, IdResolver

from config import ACCOUNT_HANDLE, ACCOUNT_PASSWORD

client = Client()
client.login(ACCOUNT_HANDLE, ACCOUNT_PASSWORD)
did = client.me.did

id_resolver = IdResolver()
