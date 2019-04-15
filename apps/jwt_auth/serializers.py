from django.conf import settings
from django.contrib.auth import authenticate, models
from django.core.exceptions import ObjectDoesNotExist
from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed

from utils.hid import HumanitarianId
from user.utils import send_account_activation
from .token import AccessToken, RefreshToken, TokenError
from .recaptcha import validate_recaptcha
from .errors import (
    InvalidCaptchaValidationError,
    AuthenticationFailedError,
    UserInactiveError,
)


class TokenObtainPairSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)
    recaptcha_response = serializers.CharField(write_only=True, required=False)

    def validate_recaptcha(self, recaptcha_response):
        if not validate_recaptcha(recaptcha_response):
            raise InvalidCaptchaValidationError

    def deactivate_account(self, user):
        if user.profile.login_attempts == settings.MAX_LOGIN_ATTEMPTS:
            send_account_activation(user)
        # if user.is_active:
        #     user.is_active = False
        #     user.save()
        #     send_account_activation(user)
        raise UserInactiveError(
            message='Account is deactivated, check your email')

    def check_login_attempts(self, user, recaptcha_response):
        login_attempts = user.profile.login_attempts
        if login_attempts >= settings.MAX_LOGIN_ATTEMPTS:
            self.deactivate_account(user)
        elif login_attempts >= settings.MAX_LOGIN_ATTEMPTS_FOR_CAPTCHA:
            self.validate_recaptcha(recaptcha_response)

    def validate(self, data):
        # NOTE: authenticate only works for active users
        user = authenticate(
            username=data['username'],
            password=data['password']
        )
        recaptcha_response = data.get('recaptcha_response')

        # user not active or user credentials don't match
        if not user or not user.is_active:
            user = models.User.objects.filter(username=data['username'])\
                .first()
            if user:
                user.profile.login_attempts += 1
                user.save()
                self.check_login_attempts(user, recaptcha_response)
                raise AuthenticationFailedError(user.profile.login_attempts)
            raise AuthenticationFailedError()

        self.check_login_attempts(user, recaptcha_response)

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
        hid = HumanitarianId(data['access_token'])

        try:
            user = hid.get_user()
        except ObjectDoesNotExist:
            raise serializers.ValidationError(
                'Error in HID Integration'
            )

        access_token = AccessToken.for_user(user)
        refresh_token = RefreshToken.for_access_token(access_token)

        return {
            'access': access_token.encode(),
            'refresh': refresh_token.encode(),
        }
