from django.contrib.auth.models import User
from django.contrib.postgres.fields import JSONField
from django.db import models, transaction
from django.dispatch import receiver

from user_resource.models import UserResource
from geo.models import Region
from user_group.models import UserGroup
from analysis_framework.models import AnalysisFramework
from category_editor.models import CategoryEditor

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
    user_groups = models.ManyToManyField(UserGroup, blank=True)
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

    @staticmethod
    def get_annotated():
        from entry.models import Lead, Entry

        pk = models.OuterRef('pk')
        user_ids = (User.objects.filter(
            project__id=models.OuterRef(pk),
        ) | User.objects.filter(
            usergroup__project__id=models.OuterRef(pk),
        )).distinct('id').values('id')

        threshold = timezone.now() - timedelta(days=30)
        return Project.objects.annotate(
            number_of_leads=models.Count('lead', distinct=True),
            number_of_entries=models.Count('lead__entry', distinct=True),

            number_of_users=models.functions.Coalesce(models.Subquery(
                User.objects.filter(id__in=models.Subquery(user_ids))
                .order_by().annotate(x=models.Value(1, models.IntegerField()))
                .values('x').annotate(c=models.Count('*')).values('c')[:1],
                output_field=models.IntegerField(),
            ), 0),

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
        return Project.get_annotated().filter(
            Project.get_query_for_member(user)
        ).distinct()

    @staticmethod
    def get_query_for_member(user):
        return (
            models.Q(members=user) |
            models.Q(user_groups__members=user)
        )

    @staticmethod
    def get_modifiable_for(user):
        return Project.get_annotated().filter(
            projectmembership__in=ProjectMembership.objects.filter(
                member=user,
                role='admin',
            )
        ).distinct()

    def can_get(self, user):
        return True

    def is_member(self, user):
        return self in Project.get_for_member(user)

    def can_modify(self, user):
        return ProjectMembership.objects.filter(
            project=self,
            member=user,
            role='admin',
        ).exists()

    def add_member(self, user, role='normal', added_by=None):
        return ProjectMembership.objects.create(
            member=user,
            role=role,
            project=self,
            added_by=added_by or user,
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
            projectmembership__role='admin'
        ).distinct()


class ProjectMembership(models.Model):
    """
    Project-Member relationship attributes
    """

    ROLES = (
        ('normal', 'Normal'),
        ('admin', 'Admin'),
    )

    member = models.ForeignKey(User, on_delete=models.CASCADE)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    role = models.CharField(max_length=96, choices=ROLES,
                            default='normal')
    joined_at = models.DateTimeField(auto_now_add=True)
    added_by = models.ForeignKey(User, on_delete=models.CASCADE,
                                 null=True, blank=True, default=None,
                                 related_name='added_project_memberships')

    def __str__(self):
        return '{} @ {}'.format(str(self.member),
                                self.project.title)

    class Meta:
        unique_together = ('member', 'project')

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
    role = models.CharField(max_length=96, choices=ProjectMembership.ROLES,
                            default='normal')
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


# Whenever a project status value is changed, update all projects' status
@receiver(models.signals.post_save, sender=ProjectStatus)
def on_status_updated(sender, **kwargs):
    with transaction.atomic():
        for project in Project.objects.all():
            project.update_status()
