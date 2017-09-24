from user.models import User
from rest_framework_simplejwt.settings import api_settings

from deep.errors import (
    UnknownTokenError,
    UserNotFoundError,
    UserInactiveError,
)


def get_user_from_token(token):
    try:
        user_id = token[api_settings.USER_ID_CLAIM]
    except KeyError:
        raise UnknownTokenError()

    try:
        user = User.objects.get(**{api_settings.USER_ID_FIELD: user_id})
    except User.DoesNotExist:
        raise UserNotFoundError()

    if not user.is_active:
        raise UserInactiveError()

    return user
