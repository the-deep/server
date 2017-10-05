from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.models import User
from django.utils.six import text_type
from django.utils.translation import ugettext_lazy as _
from rest_framework import serializers

from user.models import Profile
from utils.hid import HumanitarianId


class UserSerializer(serializers.ModelSerializer):
    organization = serializers.CharField(source='profile.organization',
                                         allow_blank=True)
    display_picture = serializers.FileField(source='profile.display_picture',
                                            allow_empty_file=True,
                                            required=False)

    class Meta:
        model = User
        fields = ('id', 'username', 'password', 'first_name', 'last_name',
                  'email', 'organization', 'display_picture',)
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        profile_data = validated_data.pop('profile', None)
        user = super(UserSerializer, self).create(validated_data)
        user.set_password(validated_data['password'])
        user.save()
        self.update_or_create_profile(user, profile_data)
        return user

    def update(self, instance, validated_data):
        profile_data = validated_data.pop('profile', None)
        user = super(UserSerializer, self).update(instance, validated_data)
        if 'password' in validated_data:
            user.set_password(validated_data['password'])
            user.save()
        self.update_or_create_profile(user, profile_data)
        return user

    def update_or_create_profile(self, user, profile_data):
        Profile.objects.update_or_create(user=user, defaults=profile_data)


class HIDTokenObtainSerializer(serializers.Serializer):
    access_token = serializers.CharField(required=True)
    expires_in = serializers.IntegerField(required=False)
    token_type = serializers.CharField(required=False)
    state = serializers.IntegerField(required=False)

    def validate(self, attrs):
        hid = HumanitarianId(attrs['access_token'])
        self.user = hid.get_user()

        # Prior to Django 1.10, inactive users could be authenticated with the
        # default `ModelBackend`.  As of Django 1.10, the `ModelBackend`
        # prevents inactive users from authenticating.  App designers can still
        # allow inactive users to authenticate by opting for the new
        # `AllowAllUsersModelBackend`.  However, we explicitly prevent inactive
        # users from authenticating to enforce a reasonable policy and provide
        # sensible backwards compatibility with older Django versions.
        if self.user is None or not self.user.is_active:
            # TODO: Better Validation Error [Also in utils/hid.py]
            raise serializers.ValidationError(
                _('No active account found with the given credentials'),
            )

        return {}


class HIDTokenObtainPairSerializer(HIDTokenObtainSerializer):
    def validate(self, attrs):
        data = super(HIDTokenObtainPairSerializer, self).validate(attrs)

        refresh = RefreshToken.for_user(self.user)

        data['refresh'] = text_type(refresh)
        data['access'] = text_type(refresh.access_token)

        return data
