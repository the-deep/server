from django.db import models
from django.contrib.postgres.fields import JSONField


class Region(models.Model):
    code = models.CharField(max_length=10)
    title = models.CharField(max_length=255)
    data = JSONField(default=None, blank=True, null=True)
    is_global = models.BooleanField(default=True)

    def __str__(self):
        return self.title


class AdminLevel(models.Model):
    region = models.ForeignKey(Region, on_delete=models.CASCADE)
    parent = models.ForeignKey('AdminLevel',
                               on_delete=models.SET_NULL,
                               null=True, blank=True, default=None)
    title = models.CharField(max_length=255)
    name_prop = models.CharField(max_length=255, blank=True)
    pcode_prop = models.CharField(max_length=255, blank=True)
    parent_name_prop = models.CharField(max_length=255, blank=True)
    parent_pcode_prop = models.CharField(max_length=255, blank=True)

    geo_shape = JSONField(default=None, blank=True, null=True)

    def __str__(self):
        return self.title


class GeoArea(models.Model):
    admin_level = models.ForeignKey(AdminLevel, on_delete=models.CASCADE)
    parent = models.ForeignKey('GeoArea',
                               on_delete=models.SET_NULL,
                               null=True, blank=True, default=None)
    title = models.CharField(max_length=255)
    data = JSONField(default=None, blank=True, null=True)
    name = models.CharField(max_length=255, blank=True)
    pcode = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return self.title
