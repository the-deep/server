from django.urls import reverse
from django.contrib.postgres.fields import ArrayField
from django.contrib.postgres.fields.jsonb import KeyTextTransform
from django.db.models.functions import Cast
from django.contrib.auth.models import User
from django.db.models import Q
from django.db import models
from django.db import connection as django_db_connection
from django_enumfield import enum

from deep.models import ProcessStatus
from user_resource.models import UserResource
from geo.models import Region
from user_group.models import UserGroup
from analysis_framework.models import AnalysisFramework
from category_editor.models import CategoryEditor
from project.permissions import PROJECT_PERMISSIONS, PROJECT_PERMISSION_MODEL_MAP
from organization.models import Organization

from django.utils import timezone
from datetime import timedelta


class Project(UserResource):
    """
    Project model
    """

    # Status Choices
    ACTIVE = 'active'
    INACTIVE = 'inactive'

    STATUS_CHOICES = (
        (ACTIVE, 'Active'),
        (INACTIVE, 'Inactive')
    )

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    start_date = models.DateField(default=None, null=True, blank=True)
    end_date = models.DateField(default=None, null=True, blank=True)

    members = models.ManyToManyField(User, blank=True,
                                     through_fields=('project', 'member'),
                                     through='ProjectMembership')
    regions = models.ManyToManyField(Region, blank=True)
    user_groups = models.ManyToManyField(
        UserGroup,
        blank=True,
        through='ProjectUserGroupMembership',
        through_fields=('project', 'usergroup'),
    )
    analysis_framework = models.ForeignKey(
        AnalysisFramework, blank=True,
        default=None, null=True,
        on_delete=models.SET_NULL,
    )
    category_editor = models.ForeignKey(
        CategoryEditor, blank=True,
        default=None, null=True,
        on_delete=models.SET_NULL,
    )
    assessment_template = models.ForeignKey(
        'ary.AssessmentTemplate',
        blank=True, default=None,
        null=True,
        on_delete=models.SET_NULL,
    )
    data = models.JSONField(default=None, blank=True, null=True)

    is_default = models.BooleanField(default=False)

    # Project visibility
    is_private = models.BooleanField(default=False)

    is_visualization_enabled = models.BooleanField(default=False)

    status = models.CharField(max_length=30,
                              choices=STATUS_CHOICES,
                              default=INACTIVE)

    organizations = models.ManyToManyField(
        Organization,
        through='ProjectOrganization',
        through_fields=('project', 'organization'),
        blank=True,
    )

    # Store project stats data as cache. View project/tasks for structure
    stats_cache = models.JSONField(default=dict)

    def __str__(self):
        return self.title

    def get_all_members(self):
        return User.objects.filter(
            projectmembership__project=self
        )

    def get_direct_members(self):
        return self.get_all_members().filter(
            projectmembership__linked_group__isnull=True
        )

    @staticmethod
    def get_annotated():
        return Project.objects.annotate(
            **{
                key: Cast(KeyTextTransform(key, 'stats_cache'), models.IntegerField())
                for key in [
                    ('number_of_leads'),
                    ('number_of_leads_tagged'),
                    ('number_of_leads_tagged_and_controlled'),
                    ('number_of_entries'),
                    ('number_of_users'),
                    # NOTE: Used for sorting in discover projects
                    ('leads_activity'),
                    ('entries_activity'),
                ]
            }
        )

    @staticmethod
    def get_for(user, annotated=False):
        # Note: `.exclude(Q(is_private=True) & ~Q(members=user)).all()`
        # excludes the the private projects that the user is not member of

        if annotated:
            return Project.get_annotated().exclude(Q(is_private=True) & ~Q(members=user))
        return Project.objects.exclude(Q(is_private=True) & ~Q(members=user))

    @classmethod
    def get_recent_activities(cls, user):
        from entry.models import Entry, EntryComment
        from lead.models import Lead

        project_qs = cls.get_for_member(user)
        created_by_expression = models.functions.Coalesce(
            models.Func(
                models.Value(' '), models.F('created_by_id__first_name'), models.F('created_by_id__last_name'),
                function='CONCAT_WS'
            ), models.F('created_by_id__email'), output_field=models.CharField()
        )

        leads_qs = Lead.objects.filter(project__in=project_qs).values_list(
            'id', 'created_at', 'project_id', 'project__title',
            'created_by_id', 'created_by__profile__display_picture__file',
            models.Value('lead', output_field=models.CharField()),
            created_by_expression,
        )
        entry_qs = Entry.objects.filter(project__in=project_qs).values_list(
            'id', 'created_at', 'project_id', 'project__title',
            'created_by_id', 'created_by__profile__display_picture__file',
            models.Value('entry', output_field=models.CharField()),
            created_by_expression,
        )
        entry_comment_qs = EntryComment.objects.filter(entry__project__in=project_qs).values_list(
            'id', 'entrycommenttext__created_at', 'entry__project_id', 'entry__project__title',
            'created_by_id', 'created_by__profile__display_picture__file',
            models.Value('entry-comment', output_field=models.CharField()),
            created_by_expression,
        ).distinct('id')

        return [
            {
                field: item[index]
                for index, field in enumerate([
                    'id',
                    'created_at',
                    'project',
                    'project_display_name',
                    'created_by',
                    'created_by_display_picture',
                    'type',
                    'created_by_display_name',
                ])
            }
            for item in leads_qs.union(entry_qs).union(entry_comment_qs).order_by('-created_at')[:30]
        ]

    @staticmethod
    def get_recent_active_projects(user, qs=None, max=3):
        # NOTE: to avoid circular import
        from entry.models import Entry
        from lead.models import Lead
        # NOTE: Django ORM union don't allow annotation
        # TODO: Need to refactor this
        with django_db_connection.cursor() as cursor:
            select_sql = [
                f'''
                    SELECT
                        tb."project_id" AS "project",
                        MAX(tb."{field}_at") AS "date"
                    FROM "{Model._meta.db_table}" AS tb
                    WHERE tb."{field}_by_id" = {user.pk}
                    GROUP BY tb."project_id"
                ''' for Model, field in [
                    (Lead, 'created'),
                    (Lead, 'modified'),
                    (Entry, 'created'),
                    (Entry, 'modified'),
                ]
            ]
            union_sql = '(' + ') UNION ('.join(select_sql) + ')'
            cursor.execute(
                f'SELECT DISTINCT(entities."project"), MAX("date") as "date" FROM ({union_sql}) as entities'
                f' GROUP BY entities."project" ORDER BY "date" DESC'
            )
            recent_projects_id = [pk for pk, _ in cursor.fetchall()]
        if qs is None:
            qs = Project.get_for_member(user)
        # only the projects user is member among the recent projects
        current_users_project_id = set(qs.filter(pk__in=recent_projects_id).values_list('pk', flat=True))
        recent_projects_id = [
            pk
            for pk in recent_projects_id
            if pk in current_users_project_id # filter out user project
        ][:max]
        projects_map = {
            project.pk: project
            for project in qs.filter(pk__in=recent_projects_id)
        }
        # Maintain the order
        recent_projects = [
            projects_map[id]
            for id in recent_projects_id if projects_map.get(id)
        ]
        return recent_projects

    @staticmethod
    def get_for_public(requestUser, user):
        return Project\
            .get_for_member(user)\
            .exclude(models.Q(is_private=True) & ~models.Q(members=requestUser))

    @staticmethod
    def get_for_member(user, annotated=False):
        # FIXME: get viewable projects
        # Also, pick only required fields instead of annotating everytime.
        project = Project.get_annotated() if annotated else Project.objects
        return project.filter(
            Project.get_query_for_member(user)
        ).distinct()

    @staticmethod
    def get_query_for_member(user):
        return models.Q(members=user)

    @staticmethod
    def get_modifiable_for(user):
        permission = PROJECT_PERMISSIONS.setup.modify
        return Project.get_annotated().filter(
            projectmembership__in=ProjectMembership.objects.filter(
                member=user,
            ).annotate(
                new_setup_permission=models.F('role__setup_permissions')
                .bitand(permission)
            ).filter(
                new_setup_permission=permission
            )
        ).distinct()

    @property
    def has_assessments(self):
        return self.assessment_template_id is not None

    def can_get(self, user):
        return self.is_member(user) or not self.is_private

    def is_member(self, user):
        return self in Project.get_for_member(user)

    def get_role(self, user):
        membership = ProjectMembership.objects.filter(
            project=self,
            member=user,
        )
        # this will return None if not exists
        return membership.first() and membership.first().role

    def can_modify(self, user):
        role = self.get_role(user)
        return role is not None and role.can_modify_setup

    def can_delete(self, user):
        role = self.get_role(user)
        return role is not None and role.can_delete_setup

    def add_member(
        self, user,
        role=None,
        added_by=None,
        linked_group=None,
        badges=None,
    ):
        if role is None:
            role = ProjectRole.get_default_role()

        return ProjectMembership.objects.create(
            member=user,
            role=role,
            project=self,
            added_by=added_by or user,
            linked_group=linked_group,
            badges=badges or [],
        )

    def get_entries_activity(self):
        return (self.stats_cache or {}).get('entries_activities') or []

    def get_leads_activity(self):
        return (self.stats_cache or {}).get('leads_activities') or []

    def get_admins(self):
        return User.objects.filter(
            projectmembership__project=self,
            projectmembership__role__in=ProjectRole.get_admin_roles(),
        ).distinct()


def get_default_role_id():
    # Query only the id column to avoid migration issues
    return ProjectRole.objects.filter(
        is_default_role=True
    ).values('id').first()['id']


class ProjectOrganization(models.Model):
    LEAD_ORGANIZATION = 'lead_organization'
    INTERNATIONAL_PARTNER = 'international_partner'
    NATIONAL_PARTNER = 'national_partner'
    DONOR = 'donor'
    GOVERNMENT = 'government'

    ORGANIZATION_TYPES = (
        (LEAD_ORGANIZATION, 'Lead Organization'),
        (INTERNATIONAL_PARTNER, 'International Partner'),
        (NATIONAL_PARTNER, 'National Partner'),
        (DONOR, 'Donor'),
        (GOVERNMENT, 'Government'),
    )

    organization_type = models.CharField(max_length=30, choices=ORGANIZATION_TYPES)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('project', 'organization_type', 'organization')


class ProjectMembership(models.Model):
    """
    Project-Member relationship attributes
    """
    class BadgeType(enum.Enum):
        QA = 0
        __labels__ = {
            QA: 'Quality Assurance',
        }

    member = models.ForeignKey(User, on_delete=models.CASCADE)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    role = models.ForeignKey(
        'project.ProjectRole',
        default=get_default_role_id,
        on_delete=models.CASCADE,
    )

    linked_group = models.ForeignKey(
        UserGroup, on_delete=models.CASCADE,
        default=None, null=True, blank=True,
    )

    joined_at = models.DateTimeField(auto_now_add=True)
    added_by = models.ForeignKey(
        User, on_delete=models.CASCADE,
        null=True, blank=True, default=None,
        related_name='added_project_memberships',
    )
    # Represents additional permission like QA
    badges = ArrayField(enum.EnumField(BadgeType), default=list, blank=True)

    class Meta:
        unique_together = ('member', 'project')

    def __str__(self):
        return '{} @ {}'.format(str(self.member),
                                self.project.title)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        group_membership = self.linked_group and \
            ProjectUserGroupMembership.objects.filter(
                usergroup=self.linked_group,
                project=self.project,
            ).first()
        if group_membership:
            role = group_membership.role or ProjectRole.get_default_role()
            if self.role != role:
                self.role = role
                self.save()

    @staticmethod
    def get_for(user):
        return ProjectMembership.objects.all()

    def can_get(self, user):
        return True

    def can_modify(self, user):
        return self.project.can_modify(user)

    def get_user_group_options(self):
        return self.project.user_groups.filter(members=self.member)


class ProjectUserGroupMembership(models.Model):
    """
    Project user group membership model
    """
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    # FIXME: use user_group instead of usergroup for consistency
    usergroup = models.ForeignKey(UserGroup, on_delete=models.CASCADE)
    role = models.ForeignKey(
        'project.ProjectRole', on_delete=models.CASCADE,
        default=get_default_role_id,
    )
    joined_at = models.DateTimeField(auto_now_add=True)
    added_by = models.ForeignKey(
        User, on_delete=models.CASCADE,
        null=True, blank=True, default=None,
        related_name='added_project_usergroups',
    )
    # Represents additional permission like QA
    badges = ArrayField(enum.EnumField(ProjectMembership.BadgeType), default=list, blank=True)

    class Meta:
        unique_together = ('usergroup', 'project')

    def __str__(self):
        return 'Group {} @ {}'.format(self.usergroup.title, self.project.title)

    @staticmethod
    def get_for(user):
        return ProjectMembership.objects.all()

    def can_get(self, user):
        return True

    def can_modify(self, user):
        return self.project.can_modify(user)


def get_default_join_request_data():
    return dict(reason='')


class ProjectJoinRequest(models.Model):
    """
    Join requests to projects and their responses
    """

    STATUSES = (
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
    )

    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    requested_by = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='project_join_requests',
    )
    requested_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=48, choices=STATUSES,
                              default='pending')
    role = models.ForeignKey('project.ProjectRole', on_delete=models.CASCADE)
    responded_by = models.ForeignKey(
        User, on_delete=models.CASCADE,
        null=True, blank=True, default=None,
        related_name='project_join_responses',
    )
    responded_at = models.DateTimeField(null=True, blank=True, default=None)
    data = models.JSONField(default=get_default_join_request_data, blank=True, null=True)

    def __str__(self):
        return 'Join request for {} by {} ({})'.format(
            self.project.title,
            self.requested_by.profile.get_display_name(),
            self.status,
        )

    class Meta:
        ordering = ('-requested_at',)


class ProjectRole(models.Model):
    """
    Roles for Project
    """

    title = models.CharField(max_length=255, unique=True)

    lead_permissions = models.IntegerField(default=0)
    entry_permissions = models.IntegerField(default=0)
    setup_permissions = models.IntegerField(default=0)
    export_permissions = models.IntegerField(default=0)
    assessment_permissions = models.IntegerField(default=0)

    level = models.IntegerField(default=0)
    is_creator_role = models.BooleanField(default=False)
    is_default_role = models.BooleanField(default=False)

    description = models.TextField(blank=True)

    @classmethod
    def get_admin_roles(cls):
        modify_bit = PROJECT_PERMISSIONS.setup.modify
        return cls.objects.annotate(
            modify_bit=models.F('setup_permissions').bitand(modify_bit)
        ).filter(modify_bit=modify_bit)

    @classmethod
    def get_creator_role(cls):
        return cls.objects.filter(is_creator_role=True).first()

    @classmethod
    def get_default_admin_role(cls):
        # TODO: This method should not be needed.
        # Fix use cases and remove this method.
        return cls.get_admin_roles().filter(
            is_creator_role=False
        ).first()

    @classmethod
    def get_default_role(cls):
        qs = cls.objects.filter(is_default_role=True)
        if qs.exists():
            return qs.first()
        return None

    def __str__(self):
        return self.title

    def __getattr__(self, name):
        if not name.startswith('can_'):
            # super() does not have __getattr__
            return super().__getattribute__(name)
        else:
            try:
                _, action, _item = name.split('_')  # Example: can_create_lead
                # TODO: Better approach
                item = PROJECT_PERMISSION_MODEL_MAP[_item]
            except ValueError:
                return super().__getattribute__(name)

            try:
                item_permissions = self.__getattr__(item + '_permissions')
            except Exception:
                raise AttributeError(
                    'No permission defined for "{}"'.format(item)
                )

            permission_bit = PROJECT_PERMISSIONS.get(item, {}).get(action)

            if permission_bit is None:
                return super().__getattribute__(name)

            # can be negative if first bit 1, so check if not zero
            return item_permissions & permission_bit != 0


class ProjectStats(models.Model):
    THRESHOLD_SECONDS = 60 * 20

    project = models.OneToOneField(Project, on_delete=models.CASCADE, related_name='entry_stats')
    modified_at = models.DateTimeField(auto_now=True)
    status = models.CharField(
        max_length=30, choices=ProcessStatus.STATUS_CHOICES, default=ProcessStatus.PENDING,
    )
    file = models.FileField(upload_to='project-stats/', max_length=255, null=True, blank=True)
    confidential_file = models.FileField(upload_to='project-stats/', max_length=255, null=True, blank=True)

    # Token is used to retrive the viz data (non-confidential)
    public_share = models.BooleanField(default=False)
    token = models.UUIDField(null=True, unique=True)

    def __str__(self):
        return str(self.project)

    @classmethod
    def get_for(cls, user):
        return cls.objects.filter(
            models.Q(project__members=user) |
            models.Q(project__user_groups__members=user)
        ).distinct()

    def get_public_url(self, request=None):
        if self.token:
            url = reverse('project-stat-viz-public', kwargs={
                'project_stat_id': self.id,
                'token': self.token,
            })
            if request:
                url = request.build_absolute_uri(url)
            return url

    def is_ready(self):
        time_threshold = timezone.now() - timedelta(seconds=self.THRESHOLD_SECONDS)
        if (
                self.status == ProcessStatus.SUCCESS and
                self.modified_at > time_threshold and
                self.file
        ):
            return True
        return False
