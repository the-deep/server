from django.utils.six import text_type
from rest_framework import HTTP_HEADER_ENCODING, authentication
from rest_framework.exceptions import AuthenticationFailed

from .token import AccessToken, TokenError


# The auth header type 'Bearer' encoded to bytes
AUTH_HEADER_TYPE_BYTES = 'Bearer'.encode(HTTP_HEADER_ENCODING)

# Paths for which no verification of access token in performed
# such as expiry verifications
# TODO: Use more generalized way to check safe path such as regex
SAFE_PATHS = ['/api/v1/token/refresh/']


class JwtAuthentication(authentication.BaseAuthentication):
    """
    JwtAuthentication for django rest framework
    """
    def authenticate_header(self, request):
        """
        Value of www-authenticate header in 401 error
        """
        return 'Bearer realm=api'

    def authenticate(self, request):
        """
        Authenticate a request using jwt and returns
        authenticated user
        """

        # Get header
        header = request.META.get('HTTP_AUTHORIZATION')
        if header is None:
            return None

        # Following two lines is needed for test client
        if isinstance(header, text_type):
            header = header.encode(HTTP_HEADER_ENCODING)

        # Get the access token from the header
        access_token = self.get_access_token(header, request)
        if not access_token:
            return None

        # Finally get the user from the token
        try:
            return (access_token.get_user(), None)
        except Exception as e:
            raise AuthenticationFailed(e.message)

    def get_access_token(self, header, request):
        """
        Parse and verity authentication header for
        access token and return the decoded jwt object
        """
        parts = header.split()

        # No Bearer header at all
        if len(parts) == 0 or parts[0] != AUTH_HEADER_TYPE_BYTES:
            return None

        # Improper Bearer header
        if len(parts) != 2:
            raise AuthenticationFailed(
                'Authorization header must be of format: Bearer <token>'
            )

        token = parts[1]

        # We got the token string, decode and return the
        # access token object
        try:
            access_token = AccessToken(token,
                                       verify=request.path not in SAFE_PATHS)
            return access_token
        except TokenError as e:
            raise AuthenticationFailed(e.message)
