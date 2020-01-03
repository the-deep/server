from django.contrib.postgres.fields import JSONField
from django.contrib.postgres.fields import ArrayField
from django.db import models

from utils.common import parse_number
from project.mixins import ProjectEntityMixin
from project.permissions import PROJECT_PERMISSIONS
from gallery.models import File
from user.models import User
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
    DATA_SERIES = 'dataSeries'  # NOTE: data saved as tabular_field id

    ENTRY_TYPES = (
        (EXCERPT, 'Excerpt'),
        (IMAGE, 'Image'),
        (DATA_SERIES, 'Data Series'),
    )

    lead = models.ForeignKey(Lead, on_delete=models.CASCADE)
    project = models.ForeignKey('project.Project', on_delete=models.CASCADE)
    order = models.IntegerField(default=1)
    analysis_framework = models.ForeignKey(
        AnalysisFramework, on_delete=models.CASCADE,
    )
    information_date = models.DateField(default=None,
                                        null=True, blank=True)

    entry_type = models.CharField(
        max_length=10,
        choices=ENTRY_TYPES,
        default=EXCERPT,
    )
    excerpt = models.TextField(blank=True)
    image = models.TextField(blank=True)
    tabular_field = models.ForeignKey(
        'tabular.Field', on_delete=models.CASCADE,
        null=True, blank=True,
    )

    dropped_excerpt = models.TextField(blank=True)
    highlight_hidden = models.BooleanField(default=False)

    @staticmethod
    def annotate_comment_count(qs):
        return qs.annotate(
            resolved_comment_count=models.Count(
                'entrycomment',
                filter=models.Q(
                    entrycomment__parent=None,
                    entrycomment__is_resolved=True,
                ),
                distinct=True,
            ),
            unresolved_comment_count=models.Count(
                'entrycomment',
                filter=models.Q(
                    entrycomment__parent=None,
                    entrycomment__is_resolved=False,
                ),
                distinct=True,
            ),
        )

    def __init__(self, *args, **kwargs):
        ret = super().__init__(*args, **kwargs)
        return ret

    def __str__(self):
        if self.entry_type == Entry.IMAGE:
            return 'Image ({})'.format(self.lead.title)
        else:
            return '"{}" ({})'.format(
                self.excerpt[:30],
                self.lead.title,
            )

    def get_image_url(self):
        if hasattr(self, 'image_url'):
            return self.image_url
        if not self.image:
            return None

        fileid = parse_number(self.image.rstrip('/').split('/')[-1])  # remove last slash if present
        if fileid is None:
            return None
        file = File.objects.filter(id=fileid).first()
        if not file:
            return None

        self.image_url = file.get_file_url()
        return self.image_url

    @classmethod
    def get_for(cls, user):
        """Entry can be only accessed by users who have access to it's
        project along with required permissions
        """
        view_unprotected_perm_value = PROJECT_PERMISSIONS.entry.view_only_unprotected
        view_perm_value = PROJECT_PERMISSIONS.entry.view

        # NOTE: This is quite complicated because user can have two view roles:
        # view entry or view_only_unprotected, both of which return different results
        qs = cls.objects.filter(
            project__projectmembership__member=user,
        ).annotate(
            # Get permission value for view_only_unprotected permission
            view_unprotected=models.F(
                'project__projectmembership__role__entry_permissions'
            ).bitand(view_unprotected_perm_value),
            # Get permission value for view permission
            view_all=models.F(
                'project__projectmembership__role__entry_permissions'
            ).bitand(view_perm_value)
        ).filter(
            # If entry is view only unprotected, filter entries with
            # lead confidentiality not confidential
            (
                models.Q(view_unprotected=view_unprotected_perm_value) &
                ~models.Q(lead__confidentiality=Lead.CONFIDENTIAL)
            ) |
            # Or, return nothing if view_all is not present
            models.Q(view_all=view_perm_value)
        )
        return qs

    @classmethod
    def get_exportable_queryset(cls, qs):
        export_unprotected_perm_value = PROJECT_PERMISSIONS.export.create_only_unprotected
        export_perm_value = PROJECT_PERMISSIONS.export.create

        return qs.annotate(
            # Get permission value for create_only_unprotected export
            create_only_unprotected=models.F(
                'project__projectmembership__role__export_permissions'
            ).bitand(export_unprotected_perm_value),
            # Get permission value for create permission
            create_all=models.F(
                'project__projectmembership__role__export_permissions'
            ).bitand(export_perm_value)
        ).filter(
            # Priority given to create_only_unprotected export permission i.e.
            # if create_only_unprotected is true, then fetch non confidential entries
            (
                models.Q(create_only_unprotected=export_unprotected_perm_value) &
                ~models.Q(lead__confidentiality=Lead.CONFIDENTIAL)
            ) |
            models.Q(create_all=export_perm_value)
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
    entry = models.ForeignKey(Entry, on_delete=models.CASCADE)
    widget = models.ForeignKey(Widget, on_delete=models.CASCADE)
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
    entry = models.ForeignKey(Entry, on_delete=models.CASCADE)
    filter = models.ForeignKey(Filter, on_delete=models.CASCADE)

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
    entry = models.ForeignKey(Entry, on_delete=models.CASCADE)
    exportable = models.ForeignKey(Exportable, on_delete=models.CASCADE)
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


class EntryComment(models.Model):
    entry = models.ForeignKey(Entry, on_delete=models.CASCADE)
    created_by = models.ForeignKey(User, related_name='%(class)s_created', on_delete=models.CASCADE)
    assignee = models.ForeignKey(User, null=True, blank=True, on_delete=models.CASCADE)
    is_resolved = models.BooleanField(null=True, blank=True, default=False)
    resolved_at = models.DateTimeField(null=True, blank=True)
    parent = models.ForeignKey(
        'EntryComment',
        null=True, blank=True, on_delete=models.CASCADE,
    )

    def __str__(self):
        return f'{self.entry}: {self.text} (Resolved: {self.is_resolved})'

    def can_delete(self, user):
        return self.can_modify(user)

    def can_modify(self, user):
        return self.created_by == user

    @staticmethod
    def get_for(user):
        return EntryComment.objects.prefetch_related('entrycommenttext_set')\
            .filter(
                models.Q(entry__lead__project__members=user) |
                models.Q(entry__lead__project__user_groups__members=user))\
            .distinct()

    @property
    def text(self):
        comment_text = self.entrycommenttext_set.last()
        if comment_text:
            return comment_text.text

    def get_related_users(self, skip_owner_user=True):
        users = list(self.entrycomment_set.values_list('created_by', flat=True).distinct())
        users.append(self.assignee_id)
        if self.parent:
            users.append(self.parent.assignee_id)
            users.append(self.parent.created_by_id)
        queryset = User.objects.filter(pk__in=users)
        if skip_owner_user:
            queryset = queryset.exclude(pk=self.created_by_id)
        return queryset


class EntryCommentText(models.Model):
    comment = models.ForeignKey(EntryComment, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    text = models.TextField()
