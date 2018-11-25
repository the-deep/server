from django.contrib.auth.models import User
from django.contrib.postgres.fields import JSONField
from django.db import models, transaction
from django.dispatch import receiver

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

        if self.and_conditions:
            return all(conditions)
        else:
            return any(conditions)


class ProjectStatusCondition(models.Model):
    NO_LEADS_CREATED = 'no_leads'
    NO_ENTRIES_CREATED = 'no_entries'

    CONDITION_TYPES = (
        (NO_LEADS_CREATED, 'No leads created since'),
        (NO_ENTRIES_CREATED, 'No entries created since'),
    )

    project_status = models.ForeignKey(ProjectStatus,
                                       related_name='conditions',
                                       on_delete=models.CASCADE)
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

        if self.condition_type == ProjectStatusCondition.NO_ENTRIES_CREATED:
            if Entry.objects.filter(
                lead__project=project,
                created_at__gt=time_threshold,
            ).exists():
                return False
            return True
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
    analysis_framework = models.ForeignKey(AnalysisFramework, blank=True,
                                           default=None, null=True,
                                           on_delete=models.SET_NULL)
    category_editor = models.ForeignKey(CategoryEditor, blank=True,
                                        default=None, null=True,
                                        on_delete=models.SET_NULL)
    assessment_template = models.ForeignKey('ary.AssessmentTemplate',
                                            blank=True, default=None,
                                            null=True,
                                            on_delete=models.SET_NULL)
    data = JSONField(default=None, blank=True, null=True)

    is_default = models.BooleanField(default=False)

    # Data for cache purposes
    status = models.ForeignKey(ProjectStatus,
                               blank=True, default=None, null=True,
                               on_delete=models.SET_NULL)

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
        return Project.objects.annotate(
            number_of_leads=models.Count('lead', distinct=True),
            number_of_entries=models.Count('lead__entry', distinct=True),

            leads_activity=models.functions.Coalesce(models.Subquery(
                Lead.objects.filter(
                    project=pk,
                    created_at__gt=threshold,
                ).order_by().values('project')
                .annotate(c=models.Count('*')).values('c')[:1],
                output_field=models.IntegerField(),
            ), 0),

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
    def get_for(user):
        return Project.get_annotated().all()

    @staticmethod
    def get_for_member(user):
        # FIXME: get viewable projects
        # Also, pick only required fields instead of annotating everytime.
        return Project.get_annotated().filter(
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
        return True

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
            role = ProjectRole.get_normal_role()

        return ProjectMembership.objects.create(
            member=user,
            role=role,
            project=self,
            added_by=added_by or user,
            linked_group=linked_group,
        )

    def calc_status(self):
        for status in ProjectStatus.objects.filter():
            if status.check_for(self):
                return status

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

        return generate_timeseries(
            Entry.objects.filter(lead__project=self).distinct(),
            min_date,
            max_date,
        )

    def get_leads_activity(self):
        min_date = timezone.now() - timedelta(days=30)
        max_date = timezone.now()

        return generate_timeseries(
            self.lead_set.all(),
            min_date,
            max_date,
        )

    def get_admins(self):
        return User.objects.filter(
            projectmembership__project=self,
            projectmembership__role=ProjectRole.get_admin_role(),
        ).distinct()

    def get_number_of_users(self):
        return User.objects.filter(
            models.Q(project=self) |
            models.Q(usergroup__project=self)
        ).distinct().count()


def get_default_role_id():
    return ProjectRole.get_normal_role().id


class ProjectMembership(models.Model):
    """
    Project-Member relationship attributes
    """

    member = models.ForeignKey(User, on_delete=models.CASCADE)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    role = models.ForeignKey('project.ProjectRole',
                             default=get_default_role_id)

    linked_group = models.ForeignKey(UserGroup,
                                     default=None, null=True, blank=True)

    joined_at = models.DateTimeField(auto_now_add=True)
    added_by = models.ForeignKey(User, on_delete=models.CASCADE,
                                 null=True, blank=True, default=None,
                                 related_name='added_project_memberships')

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
            role = group_membership.role or ProjectRole.get_normal_role()
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
    project = models.ForeignKey(Project)
    # FIXME: use user_group instead of usergroup for consistency
    usergroup = models.ForeignKey(UserGroup)
    role = models.ForeignKey('project.ProjectRole',
                             default=get_default_role_id)
    joined_at = models.DateTimeField(auto_now_add=True)
    added_by = models.ForeignKey(User, on_delete=models.CASCADE,
                                 null=True, blank=True, default=None,
                                 related_name='added_project_usergroups')

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
    requested_by = models.ForeignKey(User, on_delete=models.CASCADE,
                                     related_name='project_join_requests')
    requested_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=48, choices=STATUSES,
                              default='pending')
    role = models.ForeignKey('project.ProjectRole')
    responded_by = models.ForeignKey(User, on_delete=models.CASCADE,
                                     null=True, blank=True, default=None,
                                     related_name='project_join_responses')
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

    # NOTE: now exists independently, later might co-exist with Project
    title = models.CharField(max_length=255, unique=True)

    lead_permissions = models.IntegerField(default=0)
    entry_permissions = models.IntegerField(default=0)
    setup_permissions = models.IntegerField(default=0)
    export_permissions = models.IntegerField(default=0)
    assessment_permissions = models.IntegerField(default=0)

    is_creator_role = models.BooleanField(default=False)
    is_default_role = models.BooleanField(default=False)

    description = models.TextField(blank=True)

    @classmethod
    def get_admin_role(cls):
        qs = cls.objects.filter(is_creator_role=True)
        if qs.exists():
            return qs.first()
        return None

    @classmethod
    def get_normal_role(cls):
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


@receiver(models.signals.post_save, sender=ProjectUserGroupMembership)
def refresh_project_memberships_usergroup_modified(sender, instance, **kwargs):
    project = instance.project
    user_group = instance.usergroup

    existing_members = ProjectMembership.objects.filter(
        project=project,
        linked_group=user_group,
    )
    existing_members.update(role=instance.role)

    project_ug_members = User.objects.filter(usergroup__project=project)
    new_users = project_ug_members.difference(project.get_all_members()).\
        distinct()
    for user in new_users:
        project.add_member(user, role=instance.role, linked_group=user_group)


@receiver(models.signals.pre_delete, sender=ProjectUserGroupMembership)
def refresh_project_memberships_usergroup_removed(sender, instance, **kwargs):
    project = instance.project
    user_group = instance.usergroup

    remove_memberships = ProjectMembership.objects.filter(
        project=project,
        linked_group=user_group,
    )

    for membership in remove_memberships:
        other_user_groups = membership.get_user_group_options().exclude(
            id=user_group.id
        )
        if other_user_groups.count() > 0:
            membership.linked_group = other_user_groups.first()
            membership.save()
        else:
            membership.delete()


# Whenever a member is saved, if there is a pending request to join
# same project by same user, accept that request.
@receiver(models.signals.post_save, sender=ProjectMembership)
def on_membership_saved(sender, **kwargs):
    # if kwargs.get('created'):
    instance = kwargs.get('instance')
    ProjectJoinRequest.objects.filter(
        project=instance.project,
        requested_by=instance.member,
        status='pending',
    ).update(
        status='accepted',
        responded_by=instance.added_by,
        responded_at=instance.joined_at,
    )


# Whenever a project status value is changed, update all projects' statuses
@receiver(models.signals.post_save, sender=ProjectStatus)
@receiver(models.signals.post_delete, sender=ProjectStatus)
@receiver(models.signals.post_save, sender=ProjectStatusCondition)
def on_status_updated(sender, **kwargs):
    with transaction.atomic():
        for project in Project.objects.all():
            project.update_status()
