from django.db import models
from django.contrib.postgres.fields import JSONField


class AnalysisFramework(models.Model):
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
    schema_id = models.CharField(max_length=100)
    title = models.CharField(max_length=255)
    properties = JSONField(default=None, blank=True, null=True)

    def __str__(self):
        return self.title


class Filter(models.Model):
    """
    A filter for a widget in an analysis framework
    """
    widget = models.ForeignKey(Widget)
    title = models.CharField(max_length=255)
    properties = JSONField(default=None, blank=True, null=True)

    def __str__(self):
        return self.title


class Exportable(models.Model):
    """
    Export data for given widget
    """
    widget = models.ForeignKey(Widget)
    inline = models.BooleanField(default=False)

    def __str__(self):
        return 'Exportable for {}'.format(self.widget.title)
