from django.conf import settings
import redis

pool = None


def init():
    global pool
    pool = redis.ConnectionPool(host=settings.REDIS_STORE_HOST,
                                port=settings.REDIS_STORE_PORT,
                                db=settings.REDIS_STORE_DB)


def get_connection():
    return redis.Redis(connection_pool=pool)
