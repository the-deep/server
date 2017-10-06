from django.db import models
from django.contrib.postgres.fields import JSONField
from django.contrib.postgres.fields import ArrayField

from leads.models import Lead
from analysis_framework.models import (
    AnalysisFramework,
    Widget,
    Filter,
    Exportable,
)


class Entry(models.Model):
    """
    Entry belonging to a lead

    An entry can either be an excerpt or an image
    and contain several attributes.
    """
    lead = models.ForeignKey(Lead)
    analysis_framework = models.ForeignKey(AnalysisFramework)

    excerpt = models.TextField(blank=True)
    image = models.FileField(
        upload_to='entry-images/%Y/%m/',
        default=None, null=True, blank=True
    )

    def __str__(self):
        if self.image:
            return 'Image for {}'.format(self.lead.title)
        else:
            return '"{}" for {}'.format(
                self.excerpt[:30],
                self.lead.title,
            )


class Attribute(models.Model):
    """
    Attribute for an entry

    Note that attributes are set by widgets and has
    the reference for that widget.
    """
    entry = models.ForeignKey(Entry)
    widget = models.ForeignKey(Widget)
    data = JSONField(default=None, blank=True, null=True)

    def __str__(self):
        return 'Attribute for ({}, {})'.format(
            self.entry.lead.title,
            self.widget.title,
        )


class FilterData(models.Model):
    """
    Filter data for an entry to use for filterting
    """
    entry = models.ForeignKey(Entry)
    filter = models.ForeignKey(Filter)

    # List of text values
    values = ArrayField(
        models.CharField(max_length=100, blank=True),
        default=None, blank=True, null=True,
    )

    # Just number for numeric comparision
    number = models.IntegerField(default=None, blank=True, null=True)

    def __str__(self):
        return 'Filter data for ({}, {})'.format(
            self.entry.lead.title,
            self.filter.title,
        )


class ExportData(models.Model):
    """
    Export data for an entry
    """
    entry = models.ForeignKey(Entry)
    exportable = models.ForeignKey(Exportable)
    data = JSONField(default=None, blank=True, null=True)

    def __str__(self):
        return 'Export data for ({}, {})'.format(
            self.entry.lead.title,
            self.exportable.widget.title,
        )
