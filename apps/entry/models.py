from django.contrib.contenttypes.fields import GenericRelation
from django.contrib.postgres.aggregates.general import ArrayAgg
from django.contrib.postgres.fields import ArrayField
from django.db import models

from deep.middleware import get_current_user
from utils.common import parse_number
from project.mixins import ProjectEntityMixin
from project.permissions import PROJECT_PERMISSIONS
from gallery.models import File
from user.models import User
from user_resource.models import UserResource
from lead.models import Lead
from notification.models import Assignment
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

    class TagType(models.TextChoices):
        EXCERPT = 'excerpt', 'Excerpt',
        IMAGE = 'image', 'Image',
        DATA_SERIES = 'dataSeries', 'Data Series'  # NOTE: data saved as tabular_field id

    lead = models.ForeignKey(Lead, on_delete=models.CASCADE)
    project = models.ForeignKey('project.Project', on_delete=models.CASCADE)
    order = models.IntegerField(default=1)
    analysis_framework = models.ForeignKey(
        AnalysisFramework, on_delete=models.CASCADE,
    )
    information_date = models.DateField(default=None, null=True, blank=True)

    entry_type = models.CharField(max_length=10, choices=TagType.choices, default=TagType.EXCERPT)
    excerpt = models.TextField(blank=True)
    image = models.ForeignKey(File, on_delete=models.SET_NULL, null=True, blank=True)
    image_raw = models.TextField(blank=True)
    tabular_field = models.ForeignKey('tabular.Field', on_delete=models.CASCADE, null=True, blank=True)

    dropped_excerpt = models.TextField(blank=True)  # NOTE: Original Exceprt. Modified version is stored in excerpt
    excerpt_modified = models.BooleanField(default=False)
    highlight_hidden = models.BooleanField(default=False)

    # NOTE: verification is also called controlled in QA
    controlled = models.BooleanField(default=False, blank=True, null=True)
    controlled_changed_by = models.ForeignKey(
        User, blank=True, null=True,
        related_name='+', on_delete=models.SET_NULL)
    # NOTE: verified_by is related to review comment
    verified_by = models.ManyToManyField(User, blank=True)

    # NOTE: control is like final verified action
    def control(self, user, controlled=True):
        self.controlled = controlled
        self.controlled_changed_by = user
        self.save()

    @classmethod
    def annotate_comment_count(cls, qs):
        def _count_subquery(subquery):
            return models.functions.Coalesce(
                models.Subquery(
                    subquery.values('entry').order_by().annotate(
                        count=models.Count('id', distinct=True)
                    ).values('count')[:1],
                    output_field=models.IntegerField()
                ), 0,
            )

        current_user = get_current_user()
        verified_by_qs = cls.verified_by.through.objects.filter(entry=models.OuterRef('pk'))
        entrycomment_qs = EntryComment.objects.filter(entry=models.OuterRef('pk'), parent=None)
        return qs.annotate(
            verified_by_count=_count_subquery(verified_by_qs),
            is_verified_by_current_user=models.Exists(verified_by_qs.filter(user=current_user)),
            resolved_comment_count=_count_subquery(
                entrycomment_qs.filter(is_resolved=True)
            ),
            unresolved_comment_count=_count_subquery(
                entrycomment_qs.filter(is_resolved=False)
            ),
        )

    def __init__(self, *args, **kwargs):
        ret = super().__init__(*args, **kwargs)
        return ret

    def __str__(self):
        if self.entry_type == Entry.TagType.IMAGE:
            return 'Image ({})'.format(self.lead.title)
        else:
            return '"{}" ({})'.format(
                self.excerpt[:30],
                self.lead.title,
            )

    def save(self, *args, **kwargs):
        self.excerpt_modified = self.excerpt != self.dropped_excerpt
        super().save(*args, **kwargs)

    def get_image_url(self):
        if hasattr(self, 'image_url'):
            return self.image_url

        gallery_file = None
        if self.image:
            gallery_file = self.image
        elif self.image_raw:
            fileid = parse_number(self.image_raw.rstrip('/').split('/')[-1])  # remove last slash if present
            if fileid:
                gallery_file = File.objects.filter(id=fileid).first()
        self.image_url = gallery_file and gallery_file.get_file_url()
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
                ~models.Q(lead__confidentiality=Lead.Confidentiality.CONFIDENTIAL)
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
                ~models.Q(lead__confidentiality=Lead.Confidentiality.CONFIDENTIAL)
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
    # Widget's version when the attribute was saved (Set by client)
    widget_version = models.SmallIntegerField(null=True, blank=True)
    data = models.JSONField(default=None, blank=True, null=True)

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
    number = models.BigIntegerField(default=None, blank=True, null=True)

    # For intersection between two numbers
    from_number = models.IntegerField(default=None, blank=True, null=True)
    to_number = models.IntegerField(default=None, blank=True, null=True)
    text = models.TextField(default=None, blank=True, null=True)

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
    data = models.JSONField(default=None, blank=True, null=True)

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
    assignees = models.ManyToManyField(User, blank=True)
    is_resolved = models.BooleanField(null=True, blank=True, default=False)
    resolved_at = models.DateTimeField(null=True, blank=True)
    parent = models.ForeignKey(
        'EntryComment',
        null=True, blank=True, on_delete=models.CASCADE,
    )
    assignments = GenericRelation(Assignment, related_query_name='entry_comment')

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
        users = list(self.entrycomment_set.values_list('created_by', flat=True))
        users.extend(self.assignees.values_list('id', flat=True))
        if self.parent:
            users.extend(self.parent.assignees.values_list('id', flat=True))
            users.append(self.parent.created_by_id)
        queryset = User.objects.filter(pk__in=set(users))
        if skip_owner_user:
            queryset = queryset.exclude(pk=self.created_by_id)
        return queryset


class EntryCommentText(models.Model):
    comment = models.ForeignKey(EntryComment, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    text = models.TextField()


# For Entry Grouping Feature
class ProjectEntryLabel(UserResource):
    """
    Labels defined for entries in Project Scope
    """
    project = models.ForeignKey('project.Project', on_delete=models.CASCADE)
    title = models.CharField(max_length=225)
    order = models.IntegerField(default=1)
    color = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return f'{self.project}: {self.title}'

    def can_modify(self, user):
        return self.project.can_modify(user)


class LeadEntryGroup(UserResource):
    """
    Groups defined for entries in Lead Scope
    """
    lead = models.ForeignKey(Lead, on_delete=models.CASCADE)
    title = models.CharField(max_length=225)
    order = models.IntegerField(default=1)

    def __str__(self):
        return f'{self.lead}: {self.title}'

    def can_modify(self, user):
        return self.lead.can_modify(user)


class EntryGroupLabel(UserResource):
    """
    Relation between Groups, Labels and Entries
    """
    label = models.ForeignKey(ProjectEntryLabel, on_delete=models.CASCADE)
    group = models.ForeignKey(LeadEntryGroup, on_delete=models.CASCADE)
    entry = models.ForeignKey(Entry, on_delete=models.CASCADE)
    client_id = None

    class Meta:
        # Only single entry allowd in label:group pair
        unique_together = ('label', 'group',)

    @staticmethod
    def get_stat_for_entry(qs):
        return qs.order_by().values('entry', 'label').annotate(
            count=models.Count('id'),
            groups=ArrayAgg('group__title'),
        ).values(
            'entry', 'count', 'groups',
            label_id=models.F('label__id'),
            label_color=models.F('label__color'),
            label_title=models.F('label__title')
        )

    def __str__(self):
        return f'[{self.label}]:{self.group} -> {self.entry}'

    def can_modify(self, user):
        return self.entry.can_modify(user)
