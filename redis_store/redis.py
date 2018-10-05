from django.conf import settings
import redis


"""
Redis connection pool
"""
pool = None


def init():
    """
    Initialize the redis conneciton pool
    """
    global pool
    if pool:
        return
    pool = redis.ConnectionPool.from_url(url=settings.CELERY_REDIS_URL)


def get_connection():
    """
    Get new redis connection from the connection pool
    """
    return redis.Redis(connection_pool=pool)


def get_lock(key, timeout=None):
    client = get_connection()
    return client.lock(key, timeout=timeout)


def clean_redis_store():
    r = get_connection()
    r.flushall()
