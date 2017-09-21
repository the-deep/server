from channels.generic.websockets import JsonWebsocketConsumer
from channels import Group
from redis_store import redis


"""
List of all valid subscription channels
and their events as well as other required fields.
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
    def receive(self, content):
        try:
            r = redis.get_connection()
            redis_key = 'followers-{}'.format(self.message.reply_channel)
            path = self.path.strip('/')

            if path == 'subscribe':
                # Subscribe to a group

                # Step 1: validate, and encode
                self.validate(content)
                code = self.encode(content)

                # Step 2: Add to subscription channel group
                # and also store the group reference in the
                # redis followers list
                Group(code).add(self.message.reply_channel)
                r.lpush(redis_key, code)

                # Step 3: send a success reply with group code
                self.send({'code': code, 'success': True})

            elif path == 'unsubscribe':
                if content['channel'] == 'all':
                    # Unsubscribe from all groups
                    code = r.lpop(redis_key)
                    codes = []
                    while code:
                        code = code.decode('utf-8')
                        codes.append(code)
                        Group(code).discard(self.message.reply_channel)
                        code = r.lpop(redis_key)

                    if r.llen(redis_key) == 0:
                        r.delete(redis_key)

                    self.send({'codes': codes, 'success': True})

                else:
                    # Unsubscribe from a single group
                    self.validate(content)
                    code = self.encode(content)

                    Group(code).discard(self.message.reply_channel)

                    r.lrem(redis_key, 0, code)
                    if r.llen(redis_key) == 0:
                        r.delete(redis_key)

                    self.send({'code': code, 'success': True})

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
