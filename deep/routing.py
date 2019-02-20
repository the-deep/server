from channels.routing import route_class
from utils.websocket.dummy_consumer import DummyConsumer
from utils.websocket.subscription import SubscriptionConsumer


channel_routing = [
    route_class(DummyConsumer, path=r'/test/$'),
    route_class(SubscriptionConsumer, path=r'/subscribe/$'),
]
