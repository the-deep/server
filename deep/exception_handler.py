from django.utils import timezone
import sentry_sdk

from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status

from deep.errors import map_error_codes, WARN_EXCEPTIONS

import logging

logger = logging.getLogger(__name__)
standard_error_string = (
    'Something unexpected has occured. '
    'Please contact an admin to fix this issue.'
)


def custom_exception_handler(exc, context):
    # First the get response by django rest framework
    response = exception_handler(exc, context)

    # For 500 errors, we create new response
    if not response:
        request = context.get('request')
        if request and request.user and request.user.id:
            with sentry_sdk.configure_scope() as scope:
                scope.user = {
                    'id': request.user.id,
                    'email': request.user.email,
                }
                scope.set_extra('is_superuser', request.user.is_superuser)
        sentry_sdk.capture_exception()
        response = Response({}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # Empty the response body but keep the headers
    response.data = {}

    # Timestamp of exception
    response.data['timestamp'] = timezone.now()

    if hasattr(exc, 'status_code'):
        response.status_code = exc.status_code

    if hasattr(exc, 'code'):
        # If the raised exception defines a code, send it as
        # internal error code
        response.data['error_code'] = exc.code
    elif hasattr(exc, 'get_codes'):
        # Otherwise, try to map the exception.get_codes() value to an
        # internal error code.
        # If no internal code available, return http status code as
        # internal error code by default.
        response.data['error_code'] = map_error_codes(
            exc.get_codes(), response.status_code)
    else:
        response.data['error_code'] = response.status_code

    # Error message can be defined by the exception as message
    # or detail attributres
    # Otherwise, it is simply the stringified exception.

    errors = None
    user_error = None

    if hasattr(exc, 'message'):
        errors = exc.message
    elif hasattr(exc, 'detail'):
        if type(exc.detail) is list:
            errors = [str(error) for error in exc.detail]
        else:
            errors = exc.detail
    elif hasattr(exc, 'default_detail'):
        errors = exc.default_detail
    elif response.status_code == 404:
        errors = 'Resource not found'
    else:
        errors = str(exc)
        user_error = standard_error_string

    if hasattr(exc, 'user_message'):
        user_error = exc.user_message

    # Wrap up string error inside non-field-errors
    if isinstance(errors, str):
        errors = {
            'non_field_errors': [errors],
        }
    elif isinstance(errors, list) and all([isinstance(error, str) for error in errors]):
        errors = {
            'non_field_errors': errors,
        }

    if user_error:
        errors['internal_non_field_errors'] = errors.get('non_field_errors')
        errors['non_field_errors'] = [user_error]

    response.data['errors'] = errors

    # If there is a link available for the exception,
    # send back the link as well.
    if hasattr(exc, 'link'):
        response.data['link'] = exc.link

    # Logging
    if any([isinstance(exc, exception) for exception in WARN_EXCEPTIONS]):
        logger.warning('API Exception Warning!!', exc_info=True)
    else:
        logger.error(
            '{}.{}'.format(type(exc).__module__, type(exc).__name__),
            exc_info=True,
            extra={'request': context.get('request')},
        )

    return response
