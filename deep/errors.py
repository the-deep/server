from rest_framework import serializers
from jwt_auth.errors import (
    NOT_AUTHENTICATED,
    AUTHENTICATION_FAILED,
    TOKEN_INVALID,

    WARN_EXCEPTIONS as JWT_WARN_EXCEPTIONS,
)

error_code_map = {
    'not_authenticated': NOT_AUTHENTICATED,
    'authentication_failed': AUTHENTICATION_FAILED,
}


WARN_EXCEPTIONS = [
    serializers.ValidationError,
    *JWT_WARN_EXCEPTIONS,
]


def map_error_codes(codes, default=None):
    """
    Take in get_codes() value of drf exception
    and return a corresponding internal error code.
    """

    if isinstance(codes, str):
        return error_code_map.get(codes, default)

    if codes == {'non_field_errors': ['invalid']}:
        return TOKEN_INVALID

    return default
