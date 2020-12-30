"""
NOTE: We aren't using websocket so skiping this right now

from user.models import User
from channels.generic.websockets import WebsocketConsumer
from channels.test import ChannelTestCase, WSClient
from jwt_auth.token import AccessToken


class TestSubscription(ChannelTestCase):
    def setUp(self):
        # The web socket client to test with
        self.client = WSClient()

        # A new user for authentication
        user = User.objects.create_user(
            username='test@test.com',
            first_name='Test',
            last_name='Test',
            password='admin123',
            email='test@test.com',
        )
        user.save()

        # Get the access token for this user
        self.jwt = AccessToken.for_user(user).encode()
        self.user = user

    def connect(self):
        self.client.send_and_consume(
            'websocket.connect',
            path='/subscribe/?jwt={}'.format(self.jwt),
        )

    def test_hb(self):
        # Test the heartbeat request
        # We should get back a timestamp
        self.client.send_and_consume('websocket.receive',
                                     text={
                                         'sn': 1,
                                         'action': 'hb',
                                     },
                                     path='/subscribe/')
        response = self.client.receive()
        self.assertIsNotNone(response['timestamp'])

    def test_connection(self):
        # Test if we can connect to subscription endpoint
        self.connect()
        self.assertIsNone(self.client.receive())

    def test_permissions(self):
        # Test for permission by sending an unpermitted request
        # We should get 403
        self.connect()
        self.client.send_and_consume('websocket.receive',
                                     text={
                                         'sn': 1,
                                         'action': 'subscribe',
                                         'channel': 'leads',
                                         'event': 'onEdited',
                                         'leadId': 25,
                                     },
                                     path='/subscribe/')
        response = self.client.receive()
        self.assertEqual(response['sn'], 1)
        self.assertEqual(response['code'], 403)
        self.assertFalse(response['success'])

    def test_subscribe_unsubscribe(self):
        # Test if we can subscribe to on_new event for leads
        self.connect()
        self.client.send_and_consume('websocket.receive',
                                     text={
                                         'sn': 1,
                                         'action': 'subscribe',
                                         'channel': 'leads',
                                         'event': 'onNew',
                                         'projectId': 220,
                                     },
                                     path='/subscribe/')

        response = self.client.receive()
        self.assertEqual(response, {
            'sn': 1,
            'code': 'leads-onNew-220',
            'success': True,
        })

        # Test if we were added to the leads on_new group
        WebsocketConsumer.group_send(
            response['code'],
            {
                'a': 'b'
            })
        self.assertEqual(self.client.receive(),
                         {'a': 'b'})

        # Test if we can unsubscribe to all groups
        self.client.send_and_consume('websocket.receive',
                                     text={
                                         'sn': 1,
                                         'channel': 'all',
                                         'action': 'unsubscribe',
                                     },
                                     path='/subscribe/')
        response = self.client.receive()
        self.assertEqual(response,
                         {
                             'sn': 1,
                             'unsubscribed_codes': ['leads-onNew-220'],
                             'success': True
                         })

        # TODO: Test if we are really removed from the group

        # TODO Test single channel unsubscription instead of channel
"""
