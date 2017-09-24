from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from django.conf import settings

from deep.error_codes import map_error_codes

import logging

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    # First the get response by django rest framework
    response = exception_handler(exc, context)

    # For 500 errors, we create new response
    if not response:
        response = Response({}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # Empty the response body but keep the headers
    response.data = {}

    # Timestamp of exception
    response.data['timestamp'] = timezone.now()

    if hasattr(exc, 'code'):
        # If the raised exception defines a code, send it as
        # internal error code
        response.data['error_code'] = exc.code
    else:
        # Otherwise, try to map the exception.get_codes() value to an
        # internal error code.
        # If no internal code avaialble, return http status code as
        # internal error code by default.
        response.data['error_code'] = map_error_codes(
            exc.get_codes(), response.status_code)

    # Error message can be defined by the exception as message
    # or detail attribuets.
    # Otherwise, it is simply the stringified exception.
    if hasattr(exc, 'message'):
        response.data['error_message'] = exc.message
    elif hasattr(exc, 'detail'):
        response.data['error_message'] = exc.detail
    else:
        response.data['error_message'] = str(exc)

    # If there is a link available for the exception,
    # send back the link as well.
    if hasattr(exc, 'link'):
        response.data['link'] = exc.link

    # Logging for debugging
    if settings.DEBUG:
        import traceback
        logger.error(traceback.format_exc())

    return response
