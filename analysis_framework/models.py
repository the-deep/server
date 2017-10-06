from django.db import models
from django.contrib.postgres.fields import JSONField
from user_resource.models import UserResource


class AnalysisFramework(UserResource):
    """
    Analysis framework defining framework to do analysis

    Analysis is done to create entries out of leads.
    """
    title = models.CharField(max_length=255)


class Widget(models.Model):
    """
    Widget inserted into a framework
    """
    analysis_framework = models.ForeignKey(AnalysisFramework)
    schema_id = models.CharField(max_length=100, db_index=True)
    title = models.CharField(max_length=255)
    properties = JSONField(default=None, blank=True, null=True)

    def __str__(self):
        return '{} ({})'.format(self.title, self.schema_id)


class Filter(models.Model):
    """
    A filter for a widget in an analysis framework
    """
    analysis_framework = models.ForeignKey(AnalysisFramework)
    schema_id = models.CharField(max_length=100, db_index=True)
    title = models.CharField(max_length=255)
    properties = JSONField(default=None, blank=True, null=True)

    def __str__(self):
        return '{} ({})'.format(self.title, self.schema_id)


class Exportable(models.Model):
    """
    Export data for given widget
    """
    analysis_framework = models.ForeignKey(AnalysisFramework)
    schema_id = models.CharField(max_length=100, db_index=True)
    inline = models.BooleanField(default=False)

    def __str__(self):
        return 'Exportable ({})'.format(self.schema_id)
