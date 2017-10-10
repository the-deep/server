from user.models import User
from django.conf import settings
import datetime
import jwt

from .errors import (
    UnknownTokenError,
    UserNotFoundError,
    UserInactiveError,
)


class TokenError(Exception):
    """
    Token encode/decode error
    """
    code = 0x70531  # Trying and failing to hex-speak TOKEN

    def __init__(self, message):
        self.message = message


# Secret key to encode jwt
SECRET = settings.SECRET_KEY

# Default access token life time
ACCESS_TOKEN_LIFETIME = datetime.timedelta(minutes=15)


class Token:
    """
    Wrapper for jwt token
    """
    def __init__(self, token=None):
        """
        Initialize with given jwt string to decode or create a new one
        """

        self.token = token
        self.payload = {}

        if self.token:
            # Given token, decode it
            try:
                self.payload = jwt.decode(self.token,
                                          SECRET,
                                          algorithms=['HS256'])
            except jwt.ExpiredSignatureError:
                raise TokenError('Token is invalid or expired')
        else:
            # Not token was given, so create a new one
            # Also set proper lifetime starting now
            if self.lifetime:
                self.payload['exp'] = \
                    datetime.datetime.utcnow() + self.lifetime

        # Finally set the proper token type
        self.payload['tokenType'] = self.token_type

        # Leave rest of the payload to be set by inherited classes

    def encode(self):
        return jwt.encode(self.payload, SECRET, algorithm='HS256')\
            .decode('utf-8')

    def __repr__(self):
        return repr(self.payload)

    def __getitem__(self, key):
        return self.payload[key]

    def __setitem__(self, key, value):
        self.payload[key] = value

    def __delitem__(self, key):
        del self.payload[key]

    def __contains__(self, key):
        return key in self.payload

    def __str__(self):
        return self.encode()


class AccessToken(Token):
    """
    Access token
    """
    token_type = 'access'
    lifetime = ACCESS_TOKEN_LIFETIME

    @staticmethod
    def for_user(user):
        """
        Create access token for given user
        """
        token = AccessToken()

        token['userId'] = user.id
        token['username'] = user.username
        token['displayName'] = str(user)

        return token

    def get_user(self):
        """
        Get user from the access token
        """
        user_id = self.payload.get('userId')
        if not user_id:
            raise UnknownTokenError()

        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            raise UserNotFoundError()

        if not user.is_active:
            raise UserInactiveError()

        return user


class RefreshToken(Token):
    """
    Refresh token
    """
    token_type = 'refresh'
    lifetime = None

    @staticmethod
    def for_access_token(access_token):
        """
        Get refresh token for an access token
        """
        token = RefreshToken()

        # For now just set same user id
        token['userId'] = access_token['userId']

        return token
