from django.conf import settings
from deep import error_codes


class UserNotFoundError(Exception):
    status_code = 401
    code = error_codes.USER_NOT_FOUND
    message = 'User not found'


class UserInactiveError(Exception):
    status_code = 401
    code = error_codes.USER_INACTIVE
    message = 'User account is deactivated'

    def __init__(self, message):
        if (message):
            self.message = message


class UnknownTokenError(Exception):
    status_code = 400
    code = error_codes.TOKEN_INVALID
    message = 'Token contains no valid user identification'


class NotAuthenticatedError(Exception):
    status_code = 401
    code = error_codes.NOT_AUTHENTICATED,
    message = 'You are not authenticated'


class InvalidCaptchaError(Exception):
    status_code = 401
    code = error_codes.INVALID_CAPTCHA
    default_detail = 'Invalid captcha! Please, Try Again'


class AuthenticationFailedError(Exception):
    status_code = 400
    code = error_codes.AUTHENTICATION_FAILED
    message = 'No active account found with the given credentials'

    def __init__(self, login_attempts=None):
        if login_attempts:
            remaining = settings.MAX_LOGIN_ATTEMPTS - login_attempts
            self.message +=\
                '. You have {} login attempts remaining'.format(
                    remaining if remaining >= 0 else 0,
                )


WARN_EXCEPTIONS = [
    UserNotFoundError, UserInactiveError, UnknownTokenError,
    NotAuthenticatedError, InvalidCaptchaError, AuthenticationFailedError,
]
