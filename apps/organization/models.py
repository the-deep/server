from django.db import models
from user_resource.models import UserResource


class OrganizationType(models.Model):
    title = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.title


class Organization(UserResource):
    title = models.CharField(max_length=255)
    short_name = models.CharField(max_length=255, blank=True)
    long_name = models.CharField(max_length=512, blank=True)
    url = models.CharField(max_length=255, blank=True)

    logo = models.ForeignKey(
        'gallery.File',
        on_delete=models.SET_NULL,
        null=True, blank=True, default=None,
    )

    regions = models.ManyToManyField('geo.Region', blank=True)

    organization_type = models.ForeignKey(
        OrganizationType,
        on_delete=models.SET_NULL,
        null=True, blank=True, default=None,
    )

    verified = models.BooleanField(default=False)
    client_id = None

    def __str__(self):
        return self.title
