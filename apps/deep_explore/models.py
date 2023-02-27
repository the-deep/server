from django.db import models
from django.core.exceptions import ValidationError

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


class PublicExploreSnapshot(models.Model):
    """
    Used to store snapshot used by public dashboard
    """
    class Type(models.IntegerChoices):
        GLOBAL = 1, 'Global Snapshot'
        YEARLY_SNAPSHOT = 2, 'Yearly Snapshot'

    class GlobalType(models.IntegerChoices):
        FULL = 1, 'Full Dataset'
        TIME_SERIES = 2, 'Time Series Dataset'

    type = models.SmallIntegerField(choices=Type.choices)
    global_type = models.SmallIntegerField(choices=GlobalType.choices, null=True)
    start_date = models.DateField()
    end_date = models.DateField()
    year = models.SmallIntegerField(unique=True, null=True)
    file = models.FileField(upload_to='deep-explore/public-snapshot/', max_length=255)
    # Empty for global
    download_file = models.FileField(upload_to='deep-explore/public-excel-export/', max_length=255, blank=True)

    class Meta:
        ordering = ('type', 'year',)

    def clean(self):
        validation_set = [
            (PublicExploreSnapshot.Type.GLOBAL, PublicExploreSnapshot.GlobalType.TIME_SERIES, 'file'),
            (PublicExploreSnapshot.Type.GLOBAL, PublicExploreSnapshot.GlobalType.FULL, 'file'),
            (PublicExploreSnapshot.Type.GLOBAL, PublicExploreSnapshot.GlobalType.FULL, 'download_file'),
            (PublicExploreSnapshot.Type.YEARLY_SNAPSHOT, None, 'year'),
            (PublicExploreSnapshot.Type.YEARLY_SNAPSHOT, None, 'file'),
            (PublicExploreSnapshot.Type.YEARLY_SNAPSHOT, None, 'download_file'),
        ]
        fields = ['year', 'file', 'download_file']
        check_set = (self.type, self.global_type)
        for field in fields:
            if (*check_set, field) in validation_set:
                if getattr(self, field) is None:
                    raise ValidationError(
                        f'<Type:{self.type}>+<GlobalType:{self.global_type}> needs <field:{field}> to be defined.'
                    )
