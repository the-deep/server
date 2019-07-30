from django.contrib.auth.models import User
from django.contrib.postgres.fields import JSONField

from django.db import models
from django.db.models.functions import TruncDate
from django.db.models import Q

from deep.models import ProcessStatus
from user_resource.models import UserResource
from geo.models import Region
from user_group.models import UserGroup
from analysis_framework.models import AnalysisFramework
from category_editor.models import CategoryEditor
from project.permissions import PROJECT_PERMISSIONS

from utils.common import generate_timeseries

from django.utils import timezone
from datetime import timedelta


class ProjectStatus(models.Model):
    title = models.CharField(max_length=255)
    and_conditions = models.BooleanField(default=False)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name_plural = 'project statuses'

    def check_for(self, project):
        conditions = [
            c.check_for(project)
            for c in self.conditions.all()
        ]

        # NOTE: if there are no conditions, it should always return false
        # PS: any([]) is False, all([]) is False
        if len(conditions) <= 0:
            return False

        if self.and_conditions:
            return all(conditions)
        else:
            return any(conditions)


class ProjectStatusCondition(models.Model):
    SOME_LEADS_CREATED = 'some_leads'
    SOME_ENTRIES_CREATED = 'some_entries'
    NO_LEADS_CREATED = 'no_leads'
    NO_ENTRIES_CREATED = 'no_entries'

    CONDITION_TYPES = (
        (SOME_LEADS_CREATED, 'Some leads created since'),
        (SOME_ENTRIES_CREATED, 'Some entries created since'),
        (NO_LEADS_CREATED, 'No leads created since'),
        (NO_ENTRIES_CREATED, 'No entries created since'),
    )

    project_status = models.ForeignKey(
        ProjectStatus,
        related_name='conditions',
        on_delete=models.CASCADE,
    )
    condition_type = models.CharField(max_length=48,
                                      choices=CONDITION_TYPES)
    days = models.IntegerField()

    def __str__(self):
        condition_types = dict(ProjectStatusCondition.CONDITION_TYPES)
        return '{} : {} days'.format(
            condition_types[self.condition_type],
            self.days,
        )

    def check_for(self, project):
        from entry.models import Entry, Lead
        time_threshold = timezone.now() - timedelta(days=self.days)

        if self.condition_type == ProjectStatusCondition.NO_LEADS_CREATED:
            if Lead.objects.filter(
                project=project,
                created_at__gt=time_threshold,
            ).exists():
                return False
            return True

        if self.condition_type == ProjectStatusCondition.SOME_LEADS_CREATED:
            if Lead.objects.filter(
                project=project,
                created_at__gt=time_threshold,
            ).exists():
                return True
            return False

        if self.condition_type == ProjectStatusCondition.NO_ENTRIES_CREATED:
            if Entry.objects.filter(
                lead__project=project,
                created_at__gt=time_threshold,
            ).exists():
                return False
            return True

        if self.condition_type == ProjectStatusCondition.SOME_ENTRIES_CREATED:
            if Entry.objects.filter(
                lead__project=project,
                created_at__gt=time_threshold,
            ).exists():
                return True
            return False

        return False


class Project(UserResource):
    """
    Project model
    """

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
    data = JSONField(default=None, blank=True, null=True)

    is_default = models.BooleanField(default=False)

    # Project visibility
    is_private = models.BooleanField(default=False)

    # Data for cache purposes
    status = models.ForeignKey(
        ProjectStatus,
        blank=True, default=None, null=True,
        on_delete=models.SET_NULL,
    )

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
        from entry.models import Lead, Entry

        pk = models.OuterRef('pk')

        threshold = timezone.now() - timedelta(days=30)

        # TODO: Use count while using Django 2.1
        return Project.objects.annotate(
            number_of_leads=models.functions.Coalesce(models.Subquery(
                Lead.objects.filter(
                    project=pk,
                ).distinct().order_by().values('project')
                .annotate(c=models.Count('*')).values('c')[:1],
                output_field=models.IntegerField(),
            ), 0),

            number_of_entries=models.functions.Coalesce(models.Subquery(
                Entry.objects.filter(
                    lead__project=pk,
                ).distinct().order_by().values('lead__project')
                .annotate(c=models.Count('*')).values('c')[:1],
                output_field=models.IntegerField(),
            ), 0),

            # NOTE: Used for sorting in discover projects
            leads_activity=models.functions.Coalesce(models.Subquery(
                Lead.objects.filter(
                    project=pk,
                    created_at__gt=threshold,
                ).order_by().values('project')\
                .annotate(c=models.Count('*')).values('c')[:1],
                output_field=models.IntegerField(),
            ), 0),

            # NOTE: Used for sorting in discover projects
            entries_activity=models.functions.Coalesce(models.Subquery(
                Entry.objects.filter(
                    lead__project=pk,
                    created_at__gt=threshold,
                ).order_by().values('lead__project')
                .annotate(c=models.Count('*')).values('c')[:1],
                output_field=models.IntegerField(),
            ), 0),
        )

    @staticmethod
    def get_for(user, annotated=False):
        # Note: `.exclude(Q(is_private=True) & ~Q(members=user)).all()`
        # excludes the the private projects that the user is not member of

        if annotated:
            return Project.get_annotated().exclude(Q(is_private=True) & ~Q(members=user))
        return Project.objects.exclude(Q(is_private=True) & ~Q(members=user))

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

    def add_member(self, user,
                   role=None, added_by=None, linked_group=None):
        if role is None:
            role = ProjectRole.get_default_role()

        return ProjectMembership.objects.create(
            member=user,
            role=role,
            project=self,
            added_by=added_by or user,
            linked_group=linked_group,
        )

    def calc_status(self):
        # NOTE: the ordering of status if important
        for status in ProjectStatus.objects.filter():
            if status.check_for(self):
                return status

        # NOTE: if no conditions pass, return first status with no condition
        return ProjectStatus.objects.filter(
            conditions__isnull=True
        ).first()

    def update_status(self):
        Project.objects.filter(
            id=self.id
        ).update(
            status=self.calc_status()
        )

    def get_entries_activity(self):
        from entry.models import Entry
        min_date = timezone.now() - timedelta(days=30)
        max_date = timezone.now()

        activity = Entry.objects.filter(
            lead__project=self,
            created_at__date__gte=min_date,
            created_at__date__lte=max_date,
        ).annotate(
            date=TruncDate('created_at'),
        ).order_by().values('date').annotate(
            count=models.Count('date'),
        ).values('date', 'count')

        return generate_timeseries(activity, min_date, max_date)

    def get_leads_activity(self):
        from lead.models import Lead
        min_date = timezone.now() - timedelta(days=30)
        max_date = timezone.now()

        activity = Lead.objects.filter(
            project=self,
            created_at__date__gte=min_date,
            created_at__date__lte=max_date,
        ).annotate(
            date=TruncDate('created_at'),
        ).order_by().values('date').annotate(
            count=models.Count('date'),
        ).values('date', 'count')

        return generate_timeseries(activity, min_date, max_date)

    def get_admins(self):
        return User.objects.filter(
            projectmembership__project=self,
            projectmembership__role__in=ProjectRole.get_admin_roles(),
        ).distinct()

    def get_number_of_users(self):
        return User.objects.filter(
            models.Q(project=self) |
            models.Q(usergroup__project=self)
        ).distinct().count()


def get_default_role_id():
    # Query only the id column to avoid migration issues
    return ProjectRole.objects.filter(
        is_default_role=True
    ).values('id').first()['id']


class ProjectMembership(models.Model):
    """
    Project-Member relationship attributes
    """

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
                _, action, item = name.split('_')  # Example: can_create_lead
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


class ProjectEntryStats(models.Model):
    THRESHOLD_SECONDS = 60 * 20

    project = models.OneToOneField(
        Project, on_delete=models.CASCADE, related_name='entry_stats',
    )
    modified_at = models.DateTimeField(auto_now_add=True)
    file = models.FileField(upload_to='entry-stats/', max_length=255, null=True, blank=True)
    status = models.CharField(
        max_length=30, choices=ProcessStatus.STATUS_CHOICES, default=ProcessStatus.PENDING,
    )

    @staticmethod
    def get_for(user):
        return ProjectEntryStats.objects.filter(
            models.Q(project__members=user) |
            models.Q(project__user_groups__members=user)
        ).distinct()

    def is_ready(self):
        time_threshold = timezone.now() - timedelta(seconds=self.THRESHOLD_SECONDS)
        if (
                self.status == ProcessStatus.SUCCESS and
                self.modified_at > time_threshold and
                self.file
        ):
            return True
        return False
