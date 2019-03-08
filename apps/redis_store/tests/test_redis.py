from django.test import TestCase
from redis_store import redis


class RedisConnectionTest(TestCase):
    """
    A redis connection test
    """

    def test_set_and_del(self):
        """
        Test redis connection by writing, reading and deleting a value
        """
        r = redis.get_connection()
        r.set('foo', 'bar')
        self.assertEqual(r.get('foo'), b'bar')
        r.delete('foo')
        self.assertEqual(r.get('foo'), None)
