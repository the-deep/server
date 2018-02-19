from django.db import models
from django.contrib.postgres.fields import JSONField
from user_resource.models import UserResource

from gallery.models import File


class AnalysisFramework(UserResource):
    """
    Analysis framework defining framework to do analysis

    Analysis is done to create entries out of leads.
    """
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    snapshot_one = models.ForeignKey(File, on_delete=models.SET_NULL,
                                     related_name='page_one_framework',
                                     null=True, blank=True, default=None)
    snapshot_two = models.ForeignKey(File, on_delete=models.SET_NULL,
                                     related_name='page_two_framework',
                                     null=True, blank=True, default=None)

    def __str__(self):
        return self.title

    def clone(self, user):
        """
        Clone analysis framework along with all widgets,
        filters and exportables
        """
        analysis_framework = AnalysisFramework(
            title='{} (cloned)'.format(self.title),
            description=self.description,
        )
        analysis_framework.created_by = user
        analysis_framework.modified_by = user
        analysis_framework.save()

        [widget.clone_to(analysis_framework) for widget
         in self.widget_set.all()]

        [filter.clone_to(analysis_framework) for filter
         in self.filter_set.all()]

        [exportable.clone_to(analysis_framework) for exportable
         in self.exportable_set.all()]

        return analysis_framework

    @staticmethod
    def get_for(user):
        """
        Analysis Framework can only be accessed by users who have access to
        it's project
        """
        return AnalysisFramework.objects.filter(
            models.Q(created_by=user) |
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

    def save(self, *args, **kwargs):
        super(Widget, self).save(*args, **kwargs)
        from .utils import update_widget
        update_widget(self)

    def __str__(self):
        return '{} ({})'.format(self.title, self.widget_id)

    def clone_to(self, analysis_framework):
        widget = Widget(
            analysis_framework=analysis_framework,
            key=self.key,
            widget_id=self.widget_id,
            title=self.title,
            properties=self.properties,
        )
        widget.save()
        return widget

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
    key = models.CharField(max_length=100, db_index=True)
    widget_key = models.CharField(max_length=100)
    title = models.CharField(max_length=255)
    properties = JSONField(default=None, blank=True, null=True)
    filter_type = models.CharField(max_length=20, choices=FILTER_TYPES,
                                   default=LIST)

    class Meta:
        ordering = ['title', 'widget_key', 'key']

    def __str__(self):
        return '{} ({})'.format(self.title, self.key)

    def clone_to(self, analysis_framework):
        filter = Filter(
            analysis_framework=analysis_framework,
            key=self.key,
            widget_key=self.widget_key,
            title=self.title,
            properties=self.properties,
            filter_type=self.filter_type,
        )
        filter.save()
        return filter

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
    widget_key = models.CharField(max_length=100, db_index=True)
    inline = models.BooleanField(default=False)
    order = models.IntegerField(default=1)
    data = JSONField(default=None, blank=True, null=True)

    def __str__(self):
        return 'Exportable ({})'.format(self.widget_key)

    class Meta:
        ordering = ['order']

    def clone_to(self, analysis_framework):
        exportable = Exportable(
            analysis_framework=analysis_framework,
            widget_key=self.widget_key,
            inline=self.inline,
        )
        exportable.save()
        return exportable

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
