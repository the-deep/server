TOKEN_INVALID = 4001
NOT_AUTHENTICATED = 4011
AUTHENTICATION_FAILED = 4012

USER_INACTIVE = 4013
USER_NOT_FOUND = 4014


class UserNotFoundError(Exception):
    code = USER_NOT_FOUND
    message = 'User not found'


class UserInactiveError(Exception):
    code = USER_INACTIVE
    message = 'User not active'


class UnknownTokenError(Exception):
    code = TOKEN_INVALID
    message = 'Token contains no valid user identification'


class NotAuthenticatedError(Exception):
    code = NOT_AUTHENTICATED,
    message = 'You are not authenticated'
