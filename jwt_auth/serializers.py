from django.conf import settings
from django.contrib.auth import authenticate, models
from django.core.exceptions import ObjectDoesNotExist
from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed

from utils.hid import HumanitarianId
from .token import AccessToken, RefreshToken
from .recaptcha import validate_recaptcha


class TokenObtainPairSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)
    recaptcha_response = serializers.CharField(write_only=True, required=False)

    def validate(self, data):
        user = authenticate(
            username=data['username'],
            password=data['password']
        )

        if not user or not user.is_active:
            user = models.User.objects.filter(username=data['username'])\
                .first()
            if user:
                user.profile.login_attempts += 1
                user.save()

            if user.profile.login_attempts > settings.MAX_LOGIN_ATTEMPTS:
                if not validate_recaptcha(data['recaptcha_response']):
                    raise serializers.ValidationError(
                        'Invalid Captcha'
                    )

            raise serializers.ValidationError(
                'No active account found with the given credentials'
            )

        if user.profile.login_attempts > settings.MAX_LOGIN_ATTEMPTS:
            if not validate_recaptcha(data['recaptcha_response']):
                raise serializers.ValidationError(
                    'Invalid Captcha'
                )

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

        refresh_token = RefreshToken(data['refresh'])
        try:
            user_id = refresh_token['userId']
        except KeyError:
            raise serializers.ValidationError(
                'Token contains no valid user identification'
            )

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
