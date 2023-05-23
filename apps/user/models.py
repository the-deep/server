from django.contrib.postgres.fields import ArrayField
from django.contrib.auth.models import User
from django.db import models
from django.db.models import Q
from django.conf import settings
from django.utils import timezone

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


class EmailCondition(models.TextChoices):
    JOIN_REQUESTS = 'join_requests', 'Project join requests'
    NEWS_AND_UPDATES = 'news_and_updates', 'News and updates'
    EMAIL_COMMENT = 'email_comment', 'Entry comment updates'
    # Always send
    ACCOUNT_ACTIVATION = 'account_activation', 'Account Activation'
    PASSWORD_RESET = 'password_reset', 'Password Reset'
    PASSWORD_CHANGED = 'password_changed', 'Password Changed'


class Profile(models.Model):
    """
    User profile model

    Extra attributes for the user besides the django
    provided ones.
    """
    class EmailConditionOptOut(models.TextChoices):
        JOIN_REQUESTS = EmailCondition.JOIN_REQUESTS
        NEWS_AND_UPDATES = EmailCondition.NEWS_AND_UPDATES
        EMAIL_COMMENT = EmailCondition.EMAIL_COMMENT

    EMAIL_CONDITIONS_TYPES = [cond[0] for cond in EmailCondition.choices]

    ALWAYS_SEND_EMAIL_CONDITIONS = [
        EmailCondition.ACCOUNT_ACTIVATION,
        EmailCondition.PASSWORD_RESET,
        EmailCondition.PASSWORD_CHANGED
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
        models.CharField(max_length=128, choices=EmailConditionOptOut.choices),
        default=list,
        blank=True,
    )

    # this is used in user deletion
    deleted_at = models.DateTimeField(null=True, blank=True)
    original_data = models.JSONField(null=True, blank=True)

    # Last Activity
    last_active = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=False)

    USER_INACTIVE_AFTER_MONTHS = 6

    def __str__(self):
        return str(self.user)

    @staticmethod
    def get_user_accessible_features(user):
        try:
            user_domain = (user.email or user.username).split('@')[1]
            return Feature.objects.filter(
                Q(is_available_for_all=True) |
                Q(users=user) |
                Q(email_domains__domain_name__exact=user_domain)
            ).order_by('key').distinct()
        except IndexError:
            return Feature.objects.none()

    def get_accessible_features(self):
        return self.get_user_accessible_features(self.user)

    @staticmethod
    def have_feature_access_for_user(user, feature):
        return Profile.get_user_accessible_features(user).filter(key=feature).exists()

    @staticmethod
    def get_display_name_for_user(user):
        return user.get_full_name() or f'User#{user.pk}'

    def get_display_name(self):
        return self.get_display_name_for_user(self.user)

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

    def soft_delete(self, deleted_at=None, commit=True):
        # Snaphost stored for 30 days. (settings.USER_AND_PROJECT_DELETE_IN_DAYS)
        user = self.user
        original_data = dict(
            first_name=user.first_name,
            last_name=user.last_name,
            email=user.email,
            username=user.username,
            is_active=user.is_active,
            profile=dict(
                organization=self.organization,
                hid=self.hid,
                display_picture=self.display_picture_id,
                invalid_email=self.invalid_email,
            ),
        )
        # User Data
        user.is_active = False
        user.first_name = settings.DELETED_USER_FIRST_NAME
        user.last_name = settings.DELETED_USER_LAST_NAME
        user.email = user.username = f'user-{user.id}@{settings.DELETED_USER_EMAIL_DOMAIN}'
        # Profile Data
        self.deleted_at = deleted_at or timezone.now()
        self.original_data = original_data
        self.invalid_email = True
        self.organization = settings.DELETED_USER_ORGANIZATION
        self.hid = None
        self.display_picture = None
        if commit:
            user.save(
                update_fields=(
                    # User Data
                    'first_name',
                    'last_name',
                    'email',
                    'username',
                    'is_active',
                )
            )
            self.save(
                update_fields=(
                    # Deleted metadata
                    'deleted_at',
                    'original_data',
                    # Profile Data
                    'invalid_email',
                    'organization',
                    'hid',
                    'display_picture',
                )
            )

    @staticmethod
    def soft_delete_user(user, **kwargs):
        return user.profile.soft_delete(**kwargs)


def user_get_display_email(user):
    from .utils import generate_hidden_email

    return generate_hidden_email(user.email)


# TODO: Use Abstract User Model (Merge profile to User Table)
User.get_display_name = Profile.get_display_name_for_user
User.display_name = property(Profile.get_display_name_for_user)
User.have_feature_access = Profile.have_feature_access_for_user
User.get_accessible_features = Profile.get_user_accessible_features
User.get_display_email = user_get_display_email
User.soft_delete = Profile.soft_delete_user


def get_for_project(project):
    return User.objects.prefetch_related('profile').filter(
        models.Q(projectmembership__project=project) |
        models.Q(usergroup__in=project.user_groups.all())
    )


User.get_for_project = get_for_project


class EmailDomain(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    domain_name = models.CharField(max_length=255)

    def __str__(self):
        return f'{self.title}({self.domain_name})'


class Feature(models.Model):
    class FeatureType(models.TextChoices):
        GENERAL_ACCESS = 'general_access', 'General access'
        EXPERIMENTAL = 'experimental', 'Experimental'
        EARLY_ACCESS = 'early_access', 'Early access'

    class FeatureKey(models.TextChoices):
        PRIVATE_PROJECT = 'private_project', 'Private projects'
        TABULAR = 'tabular', 'Tabular'
        ZOOMABLE_IMAGE = 'zoomable_image', 'Zoomable image'
        POLYGON_SUPPORT_GEO = 'polygon_support_geo', 'Polygon support geo'
        ENTRY_VISUALIZATION_CONFIGURATION = 'entry_visualization_configuration', 'Entry visualization configuration'
        CONNECTORS = 'connectors', 'Unified Connectors'
        ASSISTED = 'assisted', 'Assisted Tagging'
        # Deprecated keys
        QUALITY_CONTROL = 'quality_control', 'Quality Control (Deprecated)'
        NEW_UI = 'new_ui', 'New UI (Deprecated)'
        ANALYSIS = 'analysis', 'Analysis (Deprecated)'
        QUESTIONNAIRE = 'questionnaire', 'Questionnaire Builder'

    key = models.CharField(max_length=255, unique=True, choices=FeatureKey.choices)
    title = models.CharField(max_length=255)
    feature_type = models.CharField(max_length=128, choices=FeatureType.choices, default=FeatureType.GENERAL_ACCESS)

    users = models.ManyToManyField(User, blank=True)
    email_domains = models.ManyToManyField(EmailDomain, blank=True)
    is_available_for_all = models.BooleanField(default=False)

    def __str__(self):
        return self.title


def gen_auth_proxy_model(ModelClass, _label=None):
    label = _label or ModelClass.__name__
    t_label = camelcase_to_titlecase(label)

    class Meta:
        proxy = True
        app_label = 'user'
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
