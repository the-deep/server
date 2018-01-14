from django.contrib.auth.models import User
from drf_dynamic_fields import DynamicFieldsMixin
from rest_framework import serializers
from django.contrib.auth.tokens import default_token_generator
from django.conf import settings
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.template import loader
from django.core.mail import EmailMultiAlternatives

from user.models import Profile
from gallery.models import File


class Dummy:
    def __init__(self, entries):
        self.__dict__.update(entries)


class UserSerializer(DynamicFieldsMixin, serializers.ModelSerializer):
    organization = serializers.CharField(source='profile.organization',
                                         allow_blank=True)
    display_picture = serializers.PrimaryKeyRelatedField(
        source='profile.display_picture',
        queryset=File.objects.all(),
        allow_null=True,
        required=False,
    )
    display_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('id', 'username', 'password', 'first_name', 'last_name',
                  'display_name',
                  'email', 'organization', 'display_picture',)
        extra_kwargs = {'password': {'write_only': True}}

    def get_display_name(self, user):
        return user.profile.get_display_name()

    def create(self, validated_data):
        profile_data = validated_data.pop('profile', None)
        user = super(UserSerializer, self).create(validated_data)
        user.set_password(validated_data['password'])
        user.save()
        user.profile = self.update_or_create_profile(user, profile_data)
        return user

    def update(self, instance, validated_data):
        profile_data = validated_data.pop('profile', None)
        user = super(UserSerializer, self).update(instance, validated_data)
        if 'password' in validated_data:
            user.set_password(validated_data['password'])
            user.save()
        user.profile = self.update_or_create_profile(user, profile_data)
        return user

    def update_or_create_profile(self, user, profile_data):
        profile, created = Profile.objects.update_or_create(
            user=user, defaults=profile_data
        )
        return profile


class PasswordResetSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)

    def send_mail(self, subject_template_name, email_template_name,
                  context, from_email, to_email,
                  html_email_template_name=None):
        """
        Send a django.core.mail.EmailMultiAlternatives to `to_email`.
        """
        subject = loader.render_to_string(subject_template_name, context)
        # Email subject *must not* contain newlines
        subject = ''.join(subject.splitlines())
        body = loader.render_to_string(email_template_name, context)

        email_message = EmailMultiAlternatives(
            subject, body, from_email, [to_email])
        if html_email_template_name is not None:
            html_email = loader.render_to_string(
                html_email_template_name, context)
            email_message.attach_alternative(html_email, 'text/html')

        email_message.send()

    def get_users(self, email):
        """Given an email, return matching user(s) who should receive a reset.
        This allows subclasses to more easily customize the default policies
        that prevent inactive users and users with unusable passwords from
        resetting their password.
        """
        active_users = User._default_manager.filter(**{
            '%s__iexact' % User.get_email_field_name(): email,
            'is_active': True,
        })
        return (u for u in active_users if u.has_usable_password())

    def create(self, validated_data, domain_override=None,
               subject_template_name='registration/password_reset_subject.txt',
               email_template_name='registration/password_reset_email.html',
               use_https=False, token_generator=default_token_generator,
               from_email=None, request=None, html_email_template_name=None,
               extra_email_context=None):
        """
        Generate a one-use only link for resetting password and send it to the
        user.
        """
        email = validated_data["email"]

        for user in self.get_users(email):
            if not domain_override:
                site_name = settings.DEEPER_SITE_NAME
                domain = settings.DJANGO_API_HOST
            else:
                site_name = domain = domain_override

            context = {
                'email': email,
                'domain': domain,
                'site_name': site_name,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)).decode(),
                'user': user,
                'token': token_generator.make_token(user),
                'protocol': 'https' if use_https else 'http',
                **(extra_email_context or {}),
            }

            self.send_mail(
                subject_template_name, email_template_name, context,
                from_email, email,
                html_email_template_name=html_email_template_name,
            )

            return Dummy(validated_data)
        return Dummy(validated_data)
