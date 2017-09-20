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
    pool = redis.ConnectionPool(host=settings.REDIS_STORE_HOST,
                                port=settings.REDIS_STORE_PORT,
                                db=settings.REDIS_STORE_DB)


def get_connection():
    """
    Get new redis connection from the connection pool
    """
    return redis.Redis(connection_pool=pool)
