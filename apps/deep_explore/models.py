from django.db import models

from project.models import Project
from geo.models import GeoArea


class AggregateTracker(models.Model):
    """
    Used to track aggregated data last updated status
    """
    class Type(models.IntegerChoices):
        ENTRIES_COUNT_BY_GEO_AREA = 1

    type = models.IntegerField(choices=Type.choices, unique=True)
    updated_at = models.DateTimeField(auto_now=True)
    value = models.CharField(max_length=225, null=True)

    @classmethod
    def latest(cls, _type):
        return cls.objects.get_or_create(type=_type)[0]


class EntriesCountByGeoAreaAggregate(models.Model):
    """
    Used as cache to calculate entry - geo_area stats
    """
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    geo_area = models.ForeignKey(GeoArea, on_delete=models.CASCADE)
    date = models.DateField()
    entries_count = models.IntegerField()

    class Meta:
        ordering = ('date',)
        unique_together = ('project', 'geo_area', 'date')


class PublicExploreYearSnapshot(models.Model):
    """
    Used to store yearly snapshot used by public dashboard
    """
    year = models.SmallIntegerField(unique=True)
    file = models.FileField(upload_to='deep-explore/public-snapshot/', max_length=255)
