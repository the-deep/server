from deep import error_codes
from jwt_auth.errors import WARN_EXCEPTIONS as JWT_WARN_EXCEPTIONS
from entry.errors import EntryValidationVersionMismatchError


error_code_map = {
    'not_authenticated': error_codes.NOT_AUTHENTICATED,
    'authentication_failed': error_codes.AUTHENTICATION_FAILED,
}


WARN_EXCEPTIONS = JWT_WARN_EXCEPTIONS + [
    EntryValidationVersionMismatchError,
]


def map_error_codes(codes, default=None):
    """
    Take in get_codes() value of drf exception
    and return a corresponding internal error code.
    """

    if isinstance(codes, str):
        return error_code_map.get(codes, default)

    if codes == {'non_field_errors': ['invalid']}:
        return error_codes.TOKEN_INVALID

    return default
