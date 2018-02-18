TOKEN_INVALID = 4001
NOT_AUTHENTICATED = 4011
AUTHENTICATION_FAILED = 4012
INVALID_CAPTCHA = 4004

USER_INACTIVE = 4013
USER_NOT_FOUND = 4014


class UserNotFoundError(Exception):
    status_code = 401
    code = USER_NOT_FOUND
    message = 'User not found'


class UserInactiveError(Exception):
    status_code = 401
    code = USER_INACTIVE
    message = 'User not active'


class UnknownTokenError(Exception):
    status_code = 400
    code = TOKEN_INVALID
    message = 'Token contains no valid user identification'


class NotAuthenticatedError(Exception):
    status_code = 401
    code = NOT_AUTHENTICATED,
    message = 'You are not authenticated'


class InvalidCaptchaError(Exception):
    status_code = 400
    code = INVALID_CAPTCHA
    message = 'Invalid captcha'
