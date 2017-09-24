TOKEN_INVALID = 4001
NOT_AUTHENTICATED = 4011
AUTHENTICATION_FAILED = 4012


error_code_map = {
    'not_authenticated': NOT_AUTHENTICATED,
    'authentication_failed': AUTHENTICATION_FAILED,
}


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
