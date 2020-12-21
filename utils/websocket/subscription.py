from django.conf import settings
from django.utils import timezone
from django.core.exceptions import ObjectDoesNotExist
from user.models import User

from rest_framework.renderers import JSONRenderer

from channels.generic.websockets import JsonWebsocketConsumer
from channels import Group
from jwt_auth.token import AccessToken, TokenError

from redis_store import redis
from urllib.parse import parse_qs

from deep import error_codes
from jwt_auth.errors import (
    NotAuthenticatedError,
    UserNotFoundError,
)
from .constants import subcription_channels, websocket_actions
from .permissions import permissions
from .errors import (
    SnNotProvidedError,
    ActionValueError,
    PermissionDenied,
    ChannelValueError,
    EventValueError,
    FieldValueError,
)

import logging
import json

logger = logging.getLogger(__name__)


class SubscriptionConsumer(JsonWebsocketConsumer):
    """
    A websocket consumer for path /subscribe/.

    User can subscribe to events in different subscription channels.
    Whenever an event occurs, all clients subscribed to that event
    are notified.

    This consumer also supports heartbeat requests.
    """

    channel_session = True

    def connect(self, message):
        """
        Connection point: needs to send back { accept: true }
        for user to successfully connect.
        """

        # We want to authorize the user before allowing to connect.
        if 'query_string' in self.message.content:
            # The jwt is passed in the query string
            params = parse_qs(self.message.content['query_string'])

            if 'jwt' in params:
                jwt = params['jwt'][0]

                # If the jwt is available, try to authorize
                # using it.
                try:
                    user = AccessToken(jwt).get_user()

                    # Save the user's id in the session for future requests
                    self.message.channel_session['user'] = user.pk

                    # Accept the connection only when authorized
                    self.message.reply_channel.send({'accept': True})
                    return

                except TokenError as e:

                    # AUTHENTICATION FAILED WITH GIVEN TOKEN
                    self.message.reply_channel.send({
                        'accept': False,
                        'errorCode': error_codes.AUTHENTICATION_FAILED,
                        'error': e.message,
                    })
                    return

                except Exception as e:
                    # All other types of errors like user not found
                    reply = {'accept': False}
                    if hasattr(e, 'code'):
                        reply['code'] = e.code
                    if hasattr(e, 'message'):
                        reply['error'] = str(e.message)
                    self.message.reply_channel.send(reply)

                    # Logging for debugging
                    if settings.DEBUG:
                        import traceback
                        logger.error(traceback.format_exc())
                        return

        # No jwt was passed in the query params, so raise an error
        self.message.reply_channel.send({
            'accept': False,
            'errorCode': error_codes.NOT_AUTHENTICATED,
            'error': 'JWT token not provided for authentication',
        })

    def receive(self, content):
        """
        A request is received in the websocket.

        Following actions are available:

        * subscribe
        * unsubscribe
        * hb

        While subscribing:
        - Every subscription request is serialized to a single string code.

        - Multiple clients with same code are grouped together
        in `Group(code)` so that whenever the event occurs, all clients
        listening to that event can be notified together.

        - For reference: for each client, we also store the list of groups
        (or rather list of codes) that the client has been added to.

        Note that for each request, a sequence number `sn` is provided by
        client which is then returned in the response.
        """

        sn = None
        try:
            # Sequence number
            sn = content.get('sn')
            if not sn:
                raise SnNotProvidedError()

            # The intended action of the user
            action = content.get('action')

            if action == 'hb':
                # Heartbeat is the simplest of the action
                # And only returns the current timestamp.

                # To decrease workload, we don't care about
                # any other stuffs including verifying user
                # for this action.
                self.send(json.loads(
                    JSONRenderer().render({
                        'sn': sn,
                        'timestamp': timezone.now()
                    }).decode('utf-8')
                ))
                return

            # Get the user from the session
            if 'user' not in self.message.channel_session:
                raise NotAuthenticatedError()

            user = None
            try:
                user = User.objects.get(
                    pk=self.message.channel_session['user'])
            except ObjectDoesNotExist:
                raise UserNotFoundError()

            # Get a redis connection
            r = redis.get_connection()

            # In redis, we store, for each client, the list of groups
            # the user has been added to.
            redis_key = '{}-groups'.format(self.message.reply_channel)

            # Make sure the action is provided and is valid
            if not action or action not in websocket_actions:
                raise ActionValueError()

            if action == 'subscribe':
                # Subscribe to a group

                # Step 1: validate, and encode the request
                self.validate(content)
                code = SubscriptionConsumer.encode(content)

                # Note to check for permissions while subscribing
                check_permissions = permissions.get(content['channel'])
                if check_permissions:
                    if not check_permissions(user, content['event'], content):
                        raise PermissionDenied()

                # Step 2: Add to subscription channel group
                # and also store the group reference in the
                # redis list for this client.
                Group(code).add(self.message.reply_channel)
                r.lpush(redis_key, code)

                # Step 3: send a success reply along with group code
                self.send({'sn': sn, 'code': code, 'success': True})

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
                    self.send({
                        'sn': sn,
                        'unsubscribed_codes': unsubscribed_codes,
                        'success': True,
                    })

                else:
                    # Unsubscribe from a single group
                    # The request is in similar form as subscription,
                    # so first get the code from the request.
                    self.validate(content)
                    code = SubscriptionConsumer.encode(content)

                    # Remove the client from the group
                    # Then remove the group from the redis list for the client
                    Group(code).discard(self.message.reply_channel)
                    r.lrem(redis_key, 0, code)

                    # If empty, remove the redis list
                    if r.llen(redis_key) == 0:
                        r.delete(redis_key)

                    # Reply back with the unsubscribed_codes.
                    self.send({
                        'sn': sn,
                        'unsubscribed_codes': [code],
                        'success': True
                    })

        except Exception as e:
            reply = {'success': False}
            reply['sn'] = sn

            if hasattr(e, 'code'):
                reply['code'] = e.code
            else:
                reply['code'] = 500

            if hasattr(e, 'message'):
                reply['error'] = str(e.message)
            else:
                reply['error'] = str(e)

            # Logging for debugging
            if settings.DEBUG:
                import traceback
                logger.error(traceback.format_exc())

            self.message.reply_channel.send(reply)

    def validate(self, content):
        """
        Validate the subscription json request

        An example of valid request is:

        {
            channel: leads,
            event: onNew,
            projectId: 223,
        }
        """
        channel = content.get('channel')

        if not channel:
            raise ChannelValueError()

        channel = subcription_channels.get(channel)
        if not channel:
            raise ChannelValueError()

        event = content.get('event')
        if not event:
            raise EventValueError()

        event = channel[event]
        if not event:
            raise EventValueError()

        for key in event:
            if not content.get(key):
                raise FieldValueError(key)

    @staticmethod
    def encode(data):
        """
        Encode subscription request to a string code

        An example of encoded string is "leads-onNew-223".

        See validate for example of json request.
        """
        channel = data['channel']
        event = data['event']

        code = '{}-{}'.format(channel, event)

        keys = subcription_channels[channel][event]
        for key in keys:
            code += '-{}'.format(data[key])

        return code

    @staticmethod
    def decode(code):
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
            data[key] = parts[i + 2]

        return data
