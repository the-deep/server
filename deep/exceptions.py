from django.utils.translation import gettext_lazy as _
from rest_framework import status


class CustomException(Exception):
    default_message = _('You do not have permission to perform this action.')

    def __init__(self, msg=None, *args, **kwargs):
        super().__init__(msg or self.default_message, *args, **kwargs)


class UnauthorizedException(CustomException):
    default_message = _('You are not authenticated')
    code = status.HTTP_401_UNAUTHORIZED


class PermissionDeniedException(CustomException):
    code = status.HTTP_403_FORBIDDEN
