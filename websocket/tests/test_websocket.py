from channels.test import ChannelTestCase, WSClient


class TestWebsocket(ChannelTestCase):
    def test_websocket(self):
        client = WSClient()

        client.send_and_consume('websocket.connect', path='/test/')
        self.assertIsNone(client.receive())

        client.send_and_consume('websocket.receive',
                                text={'message': 'echo'},
                                path='/test/')
        self.assertEqual(client.receive(),
                         {'message': 'echo'})
