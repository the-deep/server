from django.contrib.postgres.fields import ArrayField
from django.contrib.auth.models import User
from django.db import models
from django.db.models import Q
from django.conf import settings

from django_otp.plugins import (
    otp_static,
    otp_totp,
    otp_email,
)
from django_otp.plugins.otp_static.admin import StaticDeviceAdmin
from django_otp.plugins.otp_totp.admin import TOTPDeviceAdmin
from django_otp.plugins.otp_email.admin import EmailDeviceAdmin

from utils.common import camelcase_to_titlecase
from gallery.models import File


class Profile(models.Model):
    """
    User profile model

    Extra attributes for the user besides the django
    provided ones.
    """
    # Email Conditions
    E_ACCOUNT_ACTIVATION = 'account_activation'
    E_PASSWORD_RESET = 'password_reset'

    E_JOIN_REQUESTS = 'join_requests'
    E_NEWS_AND_UPDATES = 'news_and_updates'
    E_EMAIL_COMMENT = 'email_comment'

    EMAIL_CONDITIONS = (
        (E_JOIN_REQUESTS, 'Project join requests'),
        (E_NEWS_AND_UPDATES, 'News and updates'),
        (E_EMAIL_COMMENT, 'Entry comment updates'),
    )
    EMAIL_CONDITIONS_TYPES = [cond[0] for cond in EMAIL_CONDITIONS]

    ALWAYS_SEND_EMAIL_CONDITIONS = [
        E_ACCOUNT_ACTIVATION,
        E_PASSWORD_RESET,
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    organization = models.CharField(max_length=300, blank=True)
    hid = models.TextField(default=None, null=True, blank=True)
    # country = models.ForeignKey(Country, on_delete=models.SET_NULL)
    display_picture = models.ForeignKey(
        File, on_delete=models.SET_NULL, null=True, blank=True, default=None,
    )

    last_active_project = models.ForeignKey(
        'project.Project', null=True,
        blank=True, default=None,
        on_delete=models.SET_NULL,
    )

    language = models.CharField(
        max_length=255,
        choices=settings.LANGUAGES,
        default=settings.LANGUAGE_CODE,
    )

    login_attempts = models.IntegerField(default=0)
    invalid_email = models.BooleanField(default=False, help_text='Flagged as bounce email')
    email_opt_outs = ArrayField(
        models.CharField(max_length=128, choices=EMAIL_CONDITIONS),
        default=list,
        blank=True,
    )

    def __str__(self):
        return str(self.user)

    def get_accessible_features(self):
        user_domain = self.user.email.split('@')[1]
        return Feature.objects.filter(
            Q(users=self.user) | Q(email_domains__domain_name__exact=user_domain)
        )

    def get_display_name(self):
        return self.user.get_full_name() if self.user.first_name \
            else self.user.username

    def unsubscribe_email(self, email_type):
        if (
            email_type not in self.ALWAYS_SEND_EMAIL_CONDITIONS and
            self.is_email_subscribed_for(email_type)
        ):
            self.email_opt_outs.append(email_type)

    def is_email_subscribed_for(self, email_type):
        if (
            email_type in self.ALWAYS_SEND_EMAIL_CONDITIONS or (
                email_type in Profile.EMAIL_CONDITIONS_TYPES and
                email_type not in self.email_opt_outs
            )
        ):
            return True
        return False

    def get_fallback_language(self):
        return None
        # return settings.LANGUAGE_CODE


class EmailDomain(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    domain_name = models.CharField(max_length=255)

    def __str__(self):
        return f'{self.title}({self.domain_name})'


class Feature(models.Model):
    GENERAL_ACCESS = 'general_access'
    EXPERIMENTAL = 'experimental'
    EARLY_ACCESS = 'early_access'

    FEATURE_TYPES = (
        (GENERAL_ACCESS, 'General access'),
        (EXPERIMENTAL, 'Experimental'),
        (EARLY_ACCESS, 'Early access'),
    )

    PRIVATE_PROJECT = 'private_project'
    TABULAR = 'tabular'
    ZOOMABLE_IMAGE = 'zoomable_image'

    FEATURE_KEYS = (
        (PRIVATE_PROJECT, 'Private projects'),
        (TABULAR, 'Tabular'),
        (ZOOMABLE_IMAGE, 'Zoomable image'),
    )

    key = models.CharField(max_length=255, unique=True, choices=FEATURE_KEYS)
    title = models.CharField(max_length=255)
    feature_type = models.CharField(max_length=128, choices=FEATURE_TYPES, default=GENERAL_ACCESS)

    users = models.ManyToManyField(User, blank=True)
    email_domains = models.ManyToManyField(EmailDomain, blank=True)

    def __str__(self):
        return self.title


def gen_auth_proxy_model(ModelClass, _label=None):
    label = _label or ModelClass.__name__
    t_label = camelcase_to_titlecase(label)

    class Meta:
        proxy = True
        app_label = 'auth'
        verbose_name = f'{t_label}'
        verbose_name_plural = f'{t_label}s'
    model = type(f"{label.replace(' ', '_')}", (ModelClass,), {
        '__module__': __name__,
        'Meta': Meta,
    })
    return model


OTP_MODELS = (
    ('OTP Static', otp_static.models.StaticDevice, StaticDeviceAdmin),
    ('OTP TOTP', otp_totp.models.TOTPDevice, TOTPDeviceAdmin),
    ('OTP Email', otp_email.models.EmailDevice, EmailDeviceAdmin),
)

OTP_PROXY_MODELS = []
# Create OTP Proxy Model Dynamically
for label, model, model_admin in OTP_MODELS:
    OTP_PROXY_MODELS.append([
        gen_auth_proxy_model(model, label), model_admin,
    ])
