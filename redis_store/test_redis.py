from django.test import TestCase
from redis_store import redis


class RedisConnectionTest(TestCase):
    def test_set_and_del(self):
        r = redis.get_connection()
        r.set('foo', 'bar')
        self.assertEqual(r.get('foo'), b'bar')
        r.delete('foo')
        self.assertEqual(r.get('foo'), None)
