from django.db import models
from django.contrib.postgres.fields import JSONField
from user_resource.models import UserResource


class AnalysisFramework(UserResource):
    """
    Analysis framework defining framework to do analysis

    Analysis is done to create entries out of leads.
    """
    title = models.CharField(max_length=255)

    def __str__(self):
        return self.title

    @staticmethod
    def get_for(user):
        """
        Analysis Framework can only be accessed by users who have access to
        it's project
        """
        return AnalysisFramework.objects.filter(
            models.Q(project=None) |
            models.Q(project__members=user) |
            models.Q(project__user_groups__members=user)
        ).distinct()

    def can_get(self, user):
        return self in AnalysisFramework.get_for(user)

    def can_modify(self, user):
        """
        Analysis framework can be modified by a user if:
        * user created the framework, or
        * user is super user, or
        * the framework belongs to a project where the user is admin
        """
        import project
        return (
            self.created_by == user or
            user.is_superuser or
            project.models.ProjectMembership.objects.filter(
                project__in=self.project_set.all(),
                member=user,
                role='admin',
            ).exists()
        )


class Widget(models.Model):
    """
    Widget inserted into a framework
    """
    analysis_framework = models.ForeignKey(AnalysisFramework)
    key = models.CharField(max_length=100, default=None, blank=True, null=True)
    widget_id = models.CharField(max_length=100, db_index=True)
    title = models.CharField(max_length=255)
    properties = JSONField(default=None, blank=True, null=True)

    def __str__(self):
        return '{} ({})'.format(self.title, self.widget_id)

    @staticmethod
    def get_for(user):
        """
        Widget can only be accessed by users who have access to
        AnalysisFramework which has access to it's project
        """
        return Widget.objects.filter(
            models.Q(analysis_framework__project=None) |
            models.Q(analysis_framework__project__members=user) |
            models.Q(analysis_framework__project__user_groups__members=user)
        ).distinct()

    def can_get(self, user):
        return self.analysis_framework.can_get(user)

    def can_modify(self, user):
        return self.analysis_framework.can_modify(user)


class Filter(models.Model):
    """
    A filter for a widget in an analysis framework
    """
    NUMBER = 'number'
    LIST = 'list'

    FILTER_TYPES = (
        (NUMBER, 'Number'),
        (LIST, 'List'),
    )

    analysis_framework = models.ForeignKey(AnalysisFramework)
    widget_id = models.CharField(max_length=100, db_index=True)
    title = models.CharField(max_length=255)
    properties = JSONField(default=None, blank=True, null=True)
    filter_type = models.CharField(max_length=20, choices=FILTER_TYPES,
                                   default=LIST)

    def __str__(self):
        return '{} ({})'.format(self.title, self.widget_id)

    @staticmethod
    def get_for(user):
        """
        Filter can only be accessed by users who have access to
        AnalysisFramework which has access to it's project
        """
        return Filter.objects.filter(
            models.Q(analysis_framework__project=None) |
            models.Q(analysis_framework__project__members=user) |
            models.Q(analysis_framework__project__user_groups__members=user)
        ).distinct()

    def can_get(self, user):
        return self.analysis_framework.can_get(user)

    def can_modify(self, user):
        return self.analysis_framework.can_modify(user)


class Exportable(models.Model):
    """
    Export data for given widget
    """
    analysis_framework = models.ForeignKey(AnalysisFramework)
    widget_id = models.CharField(max_length=100, db_index=True)
    inline = models.BooleanField(default=False)

    def __str__(self):
        return 'Exportable ({})'.format(self.widget_id)

    @staticmethod
    def get_for(user):
        """
        Exportable can only be accessed by users who have access to
        AnalysisFramework which has access to it's project
        """
        return Exportable.objects.filter(
            models.Q(analysis_framework__project=None) |
            models.Q(analysis_framework__project__members=user) |
            models.Q(analysis_framework__project__user_groups__members=user)
        ).distinct()

    def can_get(self, user):
        return self.analysis_framework.can_get(user)

    def can_modify(self, user):
        return self.analysis_framework.can_modify(user)
