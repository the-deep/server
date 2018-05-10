from django.db import models


class OrganizationType(models.Model):
    title = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.title


class Organization(models.Model):
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

    def __str__(self):
        return self.title
