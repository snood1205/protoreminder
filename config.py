from decouple import config

REDIS_URL = config("REDIS_URL", default="redis://localhost:6379")
ACCOUNT_HANDLE = config("ACCOUNT_HANDLE")
ACCOUNT_PASSWORD = config("ACCOUNT_PASSWORD")
