from django.db import models
from django.contrib.postgres.fields import JSONField
from django.contrib.postgres.fields import ArrayField

from user_resource.models import UserResource
from lead.models import Lead
from analysis_framework.models import (
    AnalysisFramework,
    Widget,
    Filter,
    Exportable,
)


class Entry(UserResource):
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
            return 'Image ({})'.format(self.lead.title)
        else:
            return '"{}" ({})'.format(
                self.excerpt[:30],
                self.lead.title,
            )

    @staticmethod
    def get_for(user):
        """
        Entry can only be accessed by users who have access to
        it's lead
        """
        return Entry.objects.filter(
            models.Q(lead__project__members=user) |
            models.Q(lead__project__user_groups__members=user)
        ).distinct()

    def can_get(self, user):
        return self.lead.can_get(user)

    def can_modify(self, user):
        return self.lead.can_modify(user)

    class Meta(UserResource.Meta):
        verbose_name_plural = 'entries'


class Attribute(models.Model):
    """
    Attribute for an entry

    Note that attributes are set by widgets and has
    the reference for that widget.
    """
    entry = models.ForeignKey(Entry)
    widget = models.ForeignKey(Widget)
    data = JSONField(default=None, blank=True, null=True)

    @staticmethod
    def get_for(user):
        """
        Attribute can only be accessed by users who have access to
        it's entry
        """
        return Attribute.objects.filter(
            models.Q(entry__lead__project__members=user) |
            models.Q(entry__lead__project__user_groups__members=user)
        ).distinct()

    def can_get(self, user):
        return self.entry.can_get(user)

    def can_modify(self, user):
        return self.entry.can_modify(user)

    def __str__(self):
        return 'Attribute ({}, {})'.format(
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

    @staticmethod
    def get_for(user):
        """
        Filter data can only be accessed by users who have access to
        it's entry
        """
        return FilterData.objects.filter(
            models.Q(entry__lead__project__members=user) |
            models.Q(entry__lead__project__user_groups__members=user)
        ).distinct()

    def can_get(self, user):
        return self.entry.can_get(user)

    def can_modify(self, user):
        return self.entry.can_modify(user)

    def __str__(self):
        return 'Filter data ({}, {})'.format(
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

    @staticmethod
    def get_for(user):
        """
        Export data can only be accessed by users who have access to
        it's entry
        """
        return ExportData.objects.filter(
            models.Q(entry__lead__project__members=user) |
            models.Q(entry__lead__project__user_groups__members=user)
        ).distinct()

    def can_get(self, user):
        return self.entry.can_get(user)

    def can_modify(self, user):
        return self.entry.can_modify(user)

    def __str__(self):
        return 'Export data ({}, {})'.format(
            self.entry.lead.title,
            self.exportable.key,
        )
