from django.contrib.postgres.fields import JSONField
from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.dispatch import receiver

from project.mixins import ProjectEntityMixin
from user_resource.models import UserResource
from lead.models import Lead
from analysis_framework.models import (
    AnalysisFramework,
    Widget,
    Filter,
    Exportable,
)


class Entry(UserResource, ProjectEntityMixin):
    """
    Entry belonging to a lead

    An entry can either be an excerpt or an image
    and contain several attributes.
    """

    EXCERPT = 'excerpt'
    IMAGE = 'image'
    ENTRY_TYPES = (
        (EXCERPT, 'Excerpt'),
        (IMAGE, 'Image'),
    )

    lead = models.ForeignKey(Lead)
    project = models.ForeignKey('project.Project')
    order = models.IntegerField(default=1)
    analysis_framework = models.ForeignKey(AnalysisFramework)
    information_date = models.DateField(default=None,
                                        null=True, blank=True)

    entry_type = models.CharField(
        max_length=10,
        choices=ENTRY_TYPES,
        default=EXCERPT,
    )
    excerpt = models.TextField(blank=True)
    image = models.TextField(blank=True)

    def __str__(self):
        if self.entry_type == Entry.IMAGE:
            return 'Image ({})'.format(self.lead.title)
        else:
            return '"{}" ({})'.format(
                self.excerpt[:30],
                self.lead.title,
            )

    class Meta(UserResource.Meta):
        verbose_name_plural = 'entries'
        ordering = ['order', '-created_at']


class Attribute(models.Model):
    """
    Attribute for an entry

    Note that attributes are set by widgets and has
    the reference for that widget.
    """
    entry = models.ForeignKey(Entry)
    widget = models.ForeignKey(Widget)
    data = JSONField(default=None, blank=True, null=True)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        from .utils import update_entry_attribute
        update_entry_attribute(self)

    def __str__(self):
        return 'Attribute ({}, {})'.format(
            self.entry.lead.title,
            self.widget.title,
        )

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

    # For intersection between two numbers
    from_number = models.IntegerField(default=None, blank=True, null=True)
    to_number = models.IntegerField(default=None, blank=True, null=True)

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
        return ExportData.objects.select_related('entry__lead__project')\
            .filter(
                models.Q(entry__lead__project__members=user) |
                models.Q(entry__lead__project__user_groups__members=user))\
            .distinct()

    def can_get(self, user):
        return self.entry.can_get(user)

    def can_modify(self, user):
        return self.entry.can_modify(user)

    def __str__(self):
        return 'Export data ({}, {})'.format(
            self.entry.lead.title,
            self.exportable.widget_key,
        )


@receiver(models.signals.post_save, sender=Entry)
def on_entry_saved(sender, **kwargs):
    lead = kwargs.get('instance').lead
    # TODO After `project` is added to Entry
    # this should not use lead
    lead.project.update_status()
