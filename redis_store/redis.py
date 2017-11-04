from django.conf import settings
from redlock import RedLock
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
    pool = redis.ConnectionPool(host=settings.REDIS_STORE_HOST,
                                port=settings.REDIS_STORE_PORT,
                                db=settings.REDIS_STORE_DB)


def get_connection():
    """
    Get new redis connection from the connection pool
    """
    return redis.Redis(connection_pool=pool)


def get_lock(lock):
    """
    Get a distributed lock based on redis using RedLock algorithm
    """
    return RedLock(
        lock,
        connection_details=[
            {'connection_pool': pool},
        ]
    )
