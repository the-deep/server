import logging

from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth import authenticate
from django.conf import settings
from django.db import transaction

from drf_dynamic_fields import DynamicFieldsMixin
from rest_framework import serializers

from deep.serializers import (
    RemoveNullFieldsMixin,
    URLCachedFileField,
    WriteOnlyOnCreateSerializerMixin,
)
from utils.hid import hid
from user.models import Profile, Feature
from user.utils import (
    send_password_reset,
    send_password_changed_notification,
    get_client_ip,
    get_device_type
)
from project.models import Project
from gallery.models import File

from jwt_auth.captcha import validate_hcaptcha
from jwt_auth.errors import UserNotFoundError

from .utils import send_account_activation
from .validators import CustomMaximumLengthValidator

logger = logging.getLogger(__name__)


class NanoUserSerializer(RemoveNullFieldsMixin, serializers.ModelSerializer):
    display_name = serializers.CharField(
        source='profile.get_display_name',
        read_only=True,
    )

    class Meta:
        model = User
        fields = ('id', 'display_name')


class SimpleUserSerializer(RemoveNullFieldsMixin, serializers.ModelSerializer):
    display_name = serializers.CharField(
        source='profile.get_display_name',
        read_only=True,
    )
    display_picture = serializers.PrimaryKeyRelatedField(
        source='profile.display_picture',
        read_only=True,
    )
    display_picture_url = URLCachedFileField(
        source='profile.display_picture.file',
        read_only=True,
    )
    organization_title = serializers.CharField(
        source='profile.organization',
        read_only=True
    )

    class Meta:
        model = User
        fields = ('id', 'display_name', 'email',
                  'display_picture', 'display_picture_url',
                  'organization_title')


class UserSerializer(RemoveNullFieldsMixin, WriteOnlyOnCreateSerializerMixin,
                     DynamicFieldsMixin, serializers.ModelSerializer):
    organization = serializers.CharField(source='profile.organization',
                                         allow_blank=True)
    language = serializers.CharField(
        source='profile.language',
        allow_null=True,
        required=False,
    )
    display_picture = serializers.PrimaryKeyRelatedField(
        source='profile.display_picture',
        queryset=File.objects.all(),
        allow_null=True,
        required=False,
    )
    display_picture_url = URLCachedFileField(
        source='profile.display_picture.file',
        read_only=True,
    )
    display_name = serializers.CharField(
        source='profile.get_display_name',
        read_only=True,
    )
    last_active_project = serializers.PrimaryKeyRelatedField(
        source='profile.last_active_project',
        queryset=Project.objects.all(),
        allow_null=True,
        required=False,
    )
    email_opt_outs = serializers.ListField(
        source='profile.email_opt_outs',
        required=False,
    )
    login_attempts = serializers.IntegerField(
        source='profile.login_attempts',
        read_only=True,
    )

    hcaptcha_response = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ('id', 'username', 'first_name', 'last_name',
                  'display_name', 'last_active_project',
                  'login_attempts', 'hcaptcha_response',
                  'email', 'organization', 'display_picture',
                  'display_picture_url', 'language', 'email_opt_outs')
        write_only_on_create_fields = ('email', 'username')

    @classmethod
    def update_or_create_profile(cls, user, profile_data):
        profile, created = Profile.objects.update_or_create(
            user=user, defaults=profile_data
        )
        return profile

    def validate_hcaptcha_response(self, captcha):
        validate_hcaptcha(captcha)

    def validate_last_active_project(self, project):
        if project and not project.is_member(self.context['request'].user):
            raise serializers.ValidationError('Invalid project')
        return project

    def create(self, validated_data):
        profile_data = validated_data.pop('profile', None)
        validated_data.pop('hcaptcha_response', None)
        user = super().create(validated_data)
        user.save()
        user.profile = self.update_or_create_profile(user, profile_data)
        send_password_reset(user=user, welcome=True)
        return user

    def update(self, instance, validated_data):
        profile_data = validated_data.pop('profile', None)
        user = super().update(instance, validated_data)
        if 'password' in validated_data:
            user.set_password(validated_data['password'])
            user.save()
        user.profile = self.update_or_create_profile(user, profile_data)
        return user


class FeatureSerializer(RemoveNullFieldsMixin,
                        DynamicFieldsMixin, serializers.ModelSerializer):
    class Meta:
        model = Feature
        fields = ('key', 'title', 'feature_type')


class UserPreferencesSerializer(RemoveNullFieldsMixin,
                                serializers.ModelSerializer):
    display_picture = serializers.PrimaryKeyRelatedField(
        source='profile.display_picture',
        queryset=File.objects.all(),
        allow_null=True,
        required=False,
    )
    display_picture_url = URLCachedFileField(
        source='profile.display_picture.file',
        read_only=True,
    )
    display_name = serializers.CharField(
        source='profile.get_display_name',
        read_only=True,
    )
    last_active_project = serializers.PrimaryKeyRelatedField(
        source='profile.last_active_project',
        queryset=Project.objects.all(),
        allow_null=True,
        required=False,
    )
    language = serializers.CharField(source='profile.language',
                                     read_only=True)
    fallback_language = serializers.CharField(
        source='profile.get_fallback_language',
        read_only=True,
    )

    accessible_features = FeatureSerializer(
        source='profile.get_accessible_features',
        many=True,
        read_only=True,
    )

    class Meta:
        model = User
        fields = ('display_name', 'username', 'email', 'last_active_project',
                  'display_picture', 'display_picture_url', 'is_superuser',
                  'language', 'accessible_features', 'fallback_language',)


class PasswordResetSerializer(RemoveNullFieldsMixin,
                              serializers.Serializer):
    hcaptcha_response = serializers.CharField(required=True)
    email = serializers.EmailField(required=True)

    def get_user(self, email):
        users = User.objects.filter(email=email)
        if not users.exists():
            raise UserNotFoundError
        return users.first()

    def validate_email(self, email):
        self.get_user(email)
        return email

    def validate_hcaptcha_response(self, captcha):
        validate_hcaptcha(captcha)

    def save(self):
        email = self.validated_data["email"]
        send_password_reset(user=self.get_user(email))


class NotificationSerializer(RemoveNullFieldsMixin,
                             serializers.Serializer):
    date = serializers.DateTimeField()
    type = serializers.CharField(source='notification_type')
    details = serializers.ReadOnlyField()

    class Meta:
        ref_name = 'UserNotificationSerializer'


class ComprehensiveUserSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source='profile.get_display_name', read_only=True)
    organization = serializers.CharField(source='profile.organization', read_only=True)

    class Meta:
        model = User
        fields = ('id', 'name', 'email', 'organization',)


class EntryCommentUserSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source='profile.get_display_name', read_only=True)
    display_picture_url = URLCachedFileField(
        source='profile.display_picture.file',
        read_only=True,
    )
    organization = serializers.CharField(source='profile.organization', read_only=True)

    class Meta:
        model = User
        fields = ('id', 'name', 'email', 'organization', 'display_picture_url',)


class PasswordChangeSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True, write_only=True)
    new_password = serializers.CharField(required=True, write_only=True)

    def validate_old_password(self, password):
        user = self.context['request'].user
        if not user.check_password(password):
            raise serializers.ValidationError('Invalid Old Password')
        return password

    def validate_new_password(self, password):
        validate_password(password)
        return password

    def save(self):
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
        client_ip = get_client_ip(self.context['request'])
        device_type = get_device_type(self.context['request'])
        transaction.on_commit(
            lambda: send_password_changed_notification.delay(
                user_id=user.id,
                client_ip=client_ip,
                device_type=device_type)
        )

# ----------------------- NEW GRAPHQL SCHEME Serializers ----------------------------------


class UserNotificationSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source='profile.get_display_name', read_only=True)
    # display_picture = URLCachedFileField(source='profile.display_picture.file', read_only=True)

    class Meta:
        model = User
        fields = ('id', 'name', 'email')


class LoginSerializer(serializers.Serializer):
    email = serializers.CharField()
    password = serializers.CharField(write_only=True)
    captcha = serializers.CharField(write_only=True, required=False)

    @classmethod
    def is_captcha_required(cls, user=None, email=None):
        _user = user or User.objects.filter(email=email).first()
        return (
            _user is not None and
            _user.profile.login_attempts >= settings.MAX_LOGIN_ATTEMPTS_FOR_CAPTCHA
        )

    def validate_password(self, password):
        # this will now only handle max-length in the login
        CustomMaximumLengthValidator().validate(password=password)
        return password

    def validate(self, data):
        def _set_user_login_attempts(user, login_attempts):
            user.profile.login_attempts = login_attempts
            user.profile.save(update_fields=['login_attempts'])

        # NOTE: authenticate only works for active users
        # NOTE: username should be equal to email
        authenticate_user = authenticate(username=data['email'], password=data['password'])
        captcha = data.get('captcha')
        user = User.objects.filter(email=data['email']).first()

        # User doesn't exists in the system.
        if user is None:
            raise serializers.ValidationError('No active account found with the given credentials')

        # Validate captcha if required for requested user
        if self.is_captcha_required(user=user):
            if not captcha:
                raise serializers.ValidationError({'captcha': 'Captcha is required'})
            if not validate_hcaptcha(captcha, raise_on_error=False):
                raise serializers.ValidationError({'captcha': 'Invalid captcha! Please, Try Again'})

        # Let user retry until max login attempts is reached
        if user.profile.login_attempts < settings.MAX_LOGIN_ATTEMPTS:
            if authenticate_user is None:
                _set_user_login_attempts(user, user.profile.login_attempts + 1)
                raise serializers.ValidationError(
                    'No active account found with the given credentials.'
                    f' You have {settings.MAX_LOGIN_ATTEMPTS - user.profile.login_attempts} login attempts remaining'
                )
        else:
            # Lock account after to many attempts
            if user.profile.login_attempts == settings.MAX_LOGIN_ATTEMPTS:
                # Send email before locking account.
                _set_user_login_attempts(user, user.profile.login_attempts + 1)
                send_account_activation(user)
            raise serializers.ValidationError('Account is locked, check your email.')

        # Clear login_attempts after success authentication
        if user.profile.login_attempts > 0:
            _set_user_login_attempts(user, 0)
        return {'user': authenticate_user}


class CaptchaSerializerMixin(serializers.ModelSerializer):
    captcha = serializers.CharField(write_only=True, required=True)

    def validate_captcha(self, captcha):
        if not validate_hcaptcha(captcha, raise_on_error=False):
            raise serializers.ValidationError('Invalid captcha! Please, Try Again')


class RegisterSerializer(CaptchaSerializerMixin, serializers.ModelSerializer):
    email = serializers.EmailField(write_only=True, required=True)
    organization = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = (
            'email', 'first_name', 'last_name',
            'organization', 'captcha',
        )

    # Only this method is used for Register
    def create(self, validated_data):
        validated_data.pop('captcha')
        profile_data = {
            'organization': validated_data.pop('organization')
        }
        user = super().create(validated_data)
        user.profile = UserSerializer.update_or_create_profile(user, profile_data)
        transaction.on_commit(
            lambda: send_password_reset(user=user, welcome=True)
        )
        return user


# TODO: Rename this later to PasswordResetSerializer
class GqPasswordResetSerializer(CaptchaSerializerMixin, serializers.ModelSerializer):
    email = serializers.EmailField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ('email', 'captcha')

    def validate_email(self, email):
        if user := User.objects.filter(email=email.lower()).first():
            return user
        raise serializers.ValidationError('There is no user with that email.')

    def save(self):
        user = self.validated_data["email"]  # validate_email returning user instance
        send_password_reset(user=user)


class UserMeSerializer(serializers.ModelSerializer):
    organization = serializers.CharField(source='profile.organization', allow_blank=True, required=False)
    language = serializers.CharField(source='profile.language', allow_null=True, required=False)
    email_opt_outs = serializers.ListField(source='profile.email_opt_outs', required=False)
    last_active_project = serializers.PrimaryKeyRelatedField(
        source='profile.last_active_project',
        queryset=Project.objects.all(),
        allow_null=True,
        required=False,
    )
    display_picture = serializers.PrimaryKeyRelatedField(
        source='profile.display_picture',
        queryset=File.objects.all(),
        allow_null=True,
        required=False,
    )

    class Meta:
        model = User
        fields = (
            'id', 'first_name', 'last_name', 'organization', 'display_picture',
            'language', 'email_opt_outs', 'last_active_project'
        )

    def validate_last_active_project(self, project):
        if project and not project.is_member(self.context['request'].user):
            raise serializers.ValidationError('Invalid project')
        return project

    def validate_email_opt_outs(self, email_opt_outs):
        if email_opt_outs:
            invalid_options = [opt for opt in email_opt_outs if opt not in Profile.EMAIL_CONDITIONS_TYPES]
            if invalid_options:
                raise serializers.ValidationError('Invalid email opt outs: %s' % (','.join(invalid_options)))
        return email_opt_outs

    def validate_display_picture(self, display_picture):
        if display_picture and display_picture.created_by != self.context['request'].user:
            raise serializers.ValidationError('Display picture not found!')
        return display_picture

    def update(self, instance, validated_data):
        profile_data = validated_data.pop('profile', None)
        user = super().update(instance, validated_data)
        if 'password' in validated_data:
            user.set_password(validated_data['password'])
            user.save()
        user.profile = UserSerializer.update_or_create_profile(user, profile_data)
        return user


class HIDLoginSerializer(serializers.Serializer):
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
        return {'user': user}
