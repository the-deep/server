from django.db import models


class OrganizationType(models.Model):
    title = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return self.title


class Organization(models.Model):
    title = models.CharField(max_length=255)
    short_name = models.CharField(max_length=255, blank=True)
    long_name = models.CharField(max_length=512, blank=True)

    logo = models.ForeignKey(
        'gallery.File',
        on_delete=models.SET_NULL,
        null=True, blank=True, default=None,
    )

    country = models.ForeignKey(
        'geo.Region',
        on_delete=models.SET_NULL,
        null=True, blank=True, default=None,
    )

    organization_type = models.ForeignKey(
        OrganizationType,
        on_delete=models.SET_NULL,
        null=True, blank=True, default=None,
    )

    def __str__(self):
        return self.title
