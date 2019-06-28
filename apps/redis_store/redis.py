import redis

from deep.celery import app as celery_app


"""
Redis connection pool
"""
pool = None

SSL_REQ_MAP = {
    'CERT_NONE': 'none',
    'CERT_OPTIONAL': 'optional',
    'CERT_REQUIRED': 'required',
}


def init():
    """
    Initialize the redis conneciton pool
    """
    global pool
    if pool:
        return
    kconn = celery_app.connection()
    url = kconn.as_uri()
    ssl = kconn.ssl
    if ssl is not False and 'ssl_cert_reqs' in ssl:
        url += f"?ssl_cert_reqs:{SSL_REQ_MAP.get(ssl['ssl_cert_reqs'].name, 'optional')}"
    pool = redis.ConnectionPool.from_url(url=url)


def get_connection():
    """
    Get new redis connection from the connection pool
    """
    if pool is None:
        init()
    return redis.Redis(connection_pool=pool)


def get_lock(key, timeout=None):
    client = get_connection()
    return client.lock(key, timeout=timeout)
