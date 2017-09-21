from channels.routing import route_class
from deep.consumers import TestConsumer
from deep.subscription import SubscriptionConsumer


channel_routing = [
    route_class(TestConsumer, path=r'/test/$'),
    route_class(SubscriptionConsumer, path=r'/subscribe/$'),
    route_class(SubscriptionConsumer, path=r'/unsubscribe/$'),
]
