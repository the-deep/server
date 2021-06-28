import logging

from django.conf import settings
from django.contrib.auth import authenticate, models
from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed

from utils.hid import hid
from user.utils import send_account_activation
from .token import AccessToken, RefreshToken, TokenError
from .captcha import validate_hcaptcha
from .errors import (
    AuthenticationFailedError,
    UserInactiveError,
)
from user.validators import CustomMaximumLengthValidator

logger = logging.getLogger(__name__)


class TokenObtainPairSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)
    hcaptcha_response = serializers.CharField(write_only=True, required=False)

    def validate_password(self, password):
        # this will now only handle max-length in the login
        CustomMaximumLengthValidator().validate(password=password)
        return password

    def deactivate_account(self, user):
        if user.profile.login_attempts == settings.MAX_LOGIN_ATTEMPTS:
            send_account_activation(user)
        # if user.is_active:
        #     user.is_active = False
        #     user.save()
        #     send_account_activation(user)
        raise UserInactiveError(
            message='Account is deactivated, check your email')

    def check_login_attempts(self, user, captcha):
        login_attempts = user.profile.login_attempts
        if login_attempts >= settings.MAX_LOGIN_ATTEMPTS:
            self.deactivate_account(user)
        elif login_attempts >= settings.MAX_LOGIN_ATTEMPTS_FOR_CAPTCHA:
            validate_hcaptcha(captcha)

    def validate(self, data):
        # NOTE: authenticate only works for active users
        user = authenticate(
            username=data['username'],
            password=data['password']
        )
        captcha = data.get('hcaptcha_response')

        # user not active or user credentials don't match
        if not user or not user.is_active:
            user = models.User.objects.filter(username=data['username'])\
                .first()
            if user:
                user.profile.login_attempts += 1
                user.save()
                self.check_login_attempts(user, captcha)
                raise AuthenticationFailedError(user.profile.login_attempts)
            raise AuthenticationFailedError()

        self.check_login_attempts(user, captcha)

        if user.profile.login_attempts > 0:
            user.profile.login_attempts = 0
            user.save()

        access_token = AccessToken.for_user(user)
        refresh_token = RefreshToken.for_access_token(access_token)

        return {
            'access': access_token.encode(),
            'refresh': refresh_token.encode(),
        }


class TokenRefreshSerializer(serializers.Serializer):
    refresh = serializers.CharField()

    def validate(self, data):
        user = self.context['request'].user

        try:
            refresh_token = RefreshToken(data['refresh'])
            user_id = refresh_token['userId']
        except KeyError:
            raise serializers.ValidationError(
                'Token contains no valid user identification'
            )
        except TokenError as e:
            raise serializers.ValidationError(e.message)

        if user.id != user_id:
            raise serializers.ValidationError(
                'Invalid refresh token'
            )

        if not user.is_active:
            raise AuthenticationFailed('User not active')

        access_token = AccessToken.for_user(user)

        return {
            'access': access_token.encode(),
        }


class HIDTokenObtainPairSerializer(serializers.Serializer):
    access_token = serializers.CharField(required=True)
    expires_in = serializers.IntegerField(required=False)
    token_type = serializers.CharField(required=False)
    state = serializers.IntegerField(required=False)

    def validate(self, data):
        humanitarian_id = hid.HumanitarianId(data['access_token'])

        try:
            user = humanitarian_id.get_user()
        except hid.HIDBaseException as e:
            raise serializers.ValidationError(e.message)
        except Exception:
            logger.error('HID error', exc_info=True)
            raise serializers.ValidationError('Unexpected Error')

        access_token = AccessToken.for_user(user)
        refresh_token = RefreshToken.for_access_token(access_token)

        return {
            'access': access_token.encode(),
            'refresh': refresh_token.encode(),
        }
