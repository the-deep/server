from channels.generic.websockets import JsonWebsocketConsumer


class DummyConsumer(JsonWebsocketConsumer):
    def connection_groups(self):
        return ['dummy']

    def receive(self, content):
        self.send(content)
