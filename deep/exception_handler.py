from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if not response:
        response = Response({}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    response.data = {}
    response.data['status_code'] = response.status_code

    if hasattr(exc, 'code'):
        response.data['error_code'] = exc.code
    else:
        response.data['error_code'] = response.status_code

    if hasattr(exc, 'message'):
        response.data['error_message'] = exc.message
    else:
        response.data['error_message'] = str(exc)

    if hasattr(exc, 'link'):
        response.data['link'] = exc.link

    return response
