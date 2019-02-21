from django.apps import AppConfig
from redis_store import redis


class RedisStoreConfig(AppConfig):
    name = 'redis_store'

    def ready(self):
        redis.init()
