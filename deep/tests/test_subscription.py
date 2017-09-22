from channels.generic.websockets import WebsocketConsumer
from channels.test import ChannelTestCase, WSClient


class TestSubscription(ChannelTestCase):
    def test_leads(self):
        client = WSClient()

        # Test if we can connect to subscription endpoint
        client.send_and_consume('websocket.connect', path='/subscribe/')
        self.assertIsNone(client.receive())

        # Test if we can subscribe to on_new event for leads
        client.send_and_consume('websocket.receive',
                                text={
                                    'channel': 'leads',
                                    'event': 'on_new',
                                    'project_id': 220,
                                },
                                path='/subscribe/')

        response = client.receive()
        self.assertEqual(response,
                         {'code': 'leads-on_new-220', 'success': True})

        # Test if we were added to the leads on_new group
        WebsocketConsumer.group_send(
            response['code'],
            {
                'a': 'b'
            })
        self.assertEqual(client.receive(),
                         {'a': 'b'})

        # TODO Test if the group was added to redis follower list

        # Test if we can connect to unsubscription endpoint
        client.send_and_consume('websocket.connect', path='/unsubscribe/')
        self.assertIsNone(client.receive())

        # Test if we can unsubscribe to all groups
        client.send_and_consume('websocket.receive',
                                text={'channel': 'all'},
                                path='/unsubscribe/')
        response = client.receive()
        self.assertEqual(response,
                         {'codes': ['leads-on_new-220'], 'success': True})

        # TODO Test if the group was removed from the redis follower list
        # TODO Test single channel unsubscription instead of channel
