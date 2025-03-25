from redis import from_url
from config import REDIS_URL

redis = from_url(REDIS_URL)
