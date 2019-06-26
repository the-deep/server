from django.contrib.postgres.fields import ArrayField
from django.contrib.auth.models import User
from django.db import models
from django.db.models import Q
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings

from gallery.models import File
from project.models import Project, ProjectMembership


class Profile(models.Model):
    """
    User profile model

    Extra attributes for the user besides the django
    provided ones.
    """
    EMAIL_CONDITIONS = (
        ('join_requests', 'Project join requests'),
        ('news_and_updates', 'News and updates'),
    )
    EMAIL_CONDITIONS_TYPES = [cond[0] for cond in EMAIL_CONDITIONS]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    organization = models.CharField(max_length=300, blank=True)
    hid = models.TextField(default=None, null=True, blank=True)
    # country = models.ForeignKey(Country, on_delete=models.SET_NULL)
    display_picture = models.ForeignKey(
        File, on_delete=models.SET_NULL, null=True, blank=True, default=None,
    )

    last_active_project = models.ForeignKey(
        Project, null=True,
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
        user_accessible_features = Feature.objects.filter(
            Q(users=self.user) | Q(email_domains__domain_name__exact=user_domain)
        )

        return user_accessible_features

    def get_display_name(self):
        return self.user.get_full_name() if self.user.first_name \
            else self.user.username

    def unsubscribe_email(self, email_type):
        if email_type in Profile.EMAIL_CONDITIONS_TYPES and\
                email_type not in self.email_opt_outs:
            self.email_opt_outs.append(email_type)

    def is_email_subscribed_for(self, email_type):
        if email_type in Profile.EMAIL_CONDITIONS_TYPES and\
                email_type not in self.email_opt_outs:
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
        return str(self.title)


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
        return str(self.title)


def assign_to_default_project(user):
    """
    Get a default project if any and add the user as its member
    """
    default_projects = Project.objects.filter(is_default=True)
    for default_project in default_projects:
        ProjectMembership.objects.create(
            member=user,
            project=default_project,
            role='normal',
        )


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, created, **kwargs):
    """
    Signal to auto create or save user profile instance whenever
    the user is saved.
    """
    if created or Profile.objects.filter(user=instance).count() == 0:
        Profile.objects.create(user=instance)
        assign_to_default_project(instance)
    else:
        instance.profile.save()
