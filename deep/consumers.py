from channels.generic.websockets import JsonWebsocketConsumer


class TestConsumer(JsonWebsocketConsumer):
    def connection_groups(self):
        return ['test']

    def receive(self, content):
        self.send(content)
