from channels.generic.websockets import JsonWebsocketConsumer
from channels import Group
from redis_store import redis


"""
List of all valid subscription channels.

For each channel, the user provides an event name and
a set of other require fields that uniquely identifies
the event.
"""
subcription_channels = {
    'leads': {
        'on_new': ['project_id'],
        'on_edited': ['lead_id'],
    },
}


# Note for client: always unsubscribe to all channels at the
# beginning to ensure clean up.


class SubscriptionConsumer(JsonWebsocketConsumer):
    """
    A websocket consumer for subscribe/ and unsubscribe/ routes.

    User can subscribe to events in different subscription channels.
    Each event is uniquely identified by a *code*. Whenever an event
    occurs, all clients subscribed to that event are notified.
    """

    def receive(self, content):
        """
        A subscribe or unsubscribe request is received in the websocket.

        Note:
        - Every subscription request is serialized to a single string code.

        - Multiple clients with same code are grouped together
        in `Group(code)` so that whenever the event occurs, all the clients
        listening to that event can be notified together.

        - For reference: for each client, we also store the list of groups
        (or rather list of codes) that the client has been added to.
        """

        try:
            r = redis.get_connection()

            # In redis, we store, for each client, the list of groups
            # he has been added to.
            redis_key = '{}-groups'.format(self.message.reply_channel)

            # Subscribe or unsubscribe ?
            action = content['action']

            if not action:
                raise Exception('Action not provided')

            if action == 'subscribe':
                # Subscribe to a group

                # Step 1: validate, and encode the request
                self.validate(content)
                code = self.encode(content)

                # Step 2: Add to subscription channel group
                # and also store the group reference in the
                # redis list for the client.
                Group(code).add(self.message.reply_channel)
                r.lpush(redis_key, code)

                # Step 3: send a success reply along with group code
                self.send({'code': code, 'success': True})

            elif action == 'unsubscribe':
                if content['channel'] == 'all':
                    # Unsubscribe from all groups

                    # For this, we use the redis group list for the client.
                    # Iteratively, pop each group from the list,
                    # remove the client from the group itself.

                    # Also maintain list of codes of unsubscribed events.
                    unsubscribed_codes = []

                    code = r.lpop(redis_key)
                    while code:
                        code = code.decode('utf-8')

                        Group(code).discard(self.message.reply_channel)
                        unsubscribed_codes.append(code)

                        code = r.lpop(redis_key)

                    # If the list is empty, we may as well remove the list
                    # from the redis store.
                    if r.llen(redis_key) == 0:
                        r.delete(redis_key)

                    # Reply back with the unscubscribed_codes
                    self.send({'unsubscribed_codes': unsubscribed_codes,
                               'success': True})

                else:
                    # Unsubscribe from a single group
                    # The request is in similar form as subscription,
                    # so we get the code from the request.
                    self.validate(content)
                    code = self.encode(content)

                    # Remove the client from the group
                    # Then remove the group from the redis list for the client
                    Group(code).discard(self.message.reply_channel)
                    r.lrem(redis_key, 0, code)

                    # If empty, remove the redis list
                    if r.llen(redis_key) == 0:
                        r.delete(redis_key)

                    # Reply back with the unsubscribed_codes.
                    self.send({'unsubscribed_codes': [code], 'success': True})

        except Exception as e:
            self.send({
                'error': str(e),
                'success': False,
            })

    def validate(self, content):
        """
        Validate the subscription json request

        An example of valid request is:

        {
            channel: leads,
            event: on_new,
            project_id: 223,
        }
        """
        channel = content.get('channel')

        if not channel:
            raise Exception('Value for channel not provided')

        channel = subcription_channels.get(channel)
        if not channel:
            raise Exception('Invalid channel')

        event = content.get('event')
        if not event:
            raise Exception('Value for event not provided')

        event = channel[event]
        if not event:
            raise Exception('Invalid event')

        for key in event:
            if not content.get(key):
                raise Exception('Value for {} not provided'.format(key))

    def encode(self, data):
        """
        Encode subscription request to a string code

        An example of encoded string is "leads:on_new:223".

        See validate for example of json request.
        """
        channel = data['channel']
        event = data['event']

        code = '{}-{}'.format(channel, event)

        keys = subcription_channels[channel][event]
        for key in keys:
            code += '-{}'.format(data[key])

        return code

    def decode(self, code):
        """
        Decode subscription request string code to json

        See encode for example of encoded string and validate
        for example of json request.
        """
        parts = code.split('-')

        channel = parts[0]
        event = parts[1]

        data = {
            'channel': channel,
            'event': event,
        }

        keys = subcription_channels[channel][event]
        for i, key in enumerate(keys):
            data[key] = parts[i+2]

        return data
