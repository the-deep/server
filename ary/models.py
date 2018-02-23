from django.db import models
from django.contrib.postgres.fields import JSONField

from user_resource.models import UserResource
from deep.models import Field, FieldOption
from lead.models import Lead


class AssessmentTemplate(UserResource):
    title = models.CharField(max_length=255)

    def __str__(self):
        return self.title


class MetadataGroup(models.Model):
    template = models.ForeignKey(AssessmentTemplate)
    title = models.CharField(max_length=255)
    order = models.IntegerField(default=1)

    def __str__(self):
        return '{} ({})'.format(self.title, self.template)

    class Meta:
        ordering = ['order']


class MetadataField(Field):
    group = models.ForeignKey(MetadataGroup)
    order = models.IntegerField(default=1)

    def __str__(self):
        return '{} ({})'.format(self.title, self.group.template)

    class Meta(Field.Meta):
        ordering = ['order']


class MetadataOption(FieldOption):
    field = models.ForeignKey(MetadataField)
    order = models.IntegerField(default=1)

    def __str__(self):
        return 'Option {} for {}'.format(self.title, self.field)

    class Meta(FieldOption.Meta):
        ordering = ['order']


class MethodologyGroup(models.Model):
    template = models.ForeignKey(AssessmentTemplate)
    title = models.CharField(max_length=255)
    order = models.IntegerField(default=1)

    def __str__(self):
        return '{} ({})'.format(self.title, self.template)

    class Meta:
        ordering = ['order']


class MethodologyField(Field):
    group = models.ForeignKey(MethodologyGroup)
    order = models.IntegerField(default=1)

    def __str__(self):
        return '{} ({})'.format(self.title, self.group.template)

    class Meta(Field.Meta):
        ordering = ['order']


class MethodologyOption(FieldOption):
    field = models.ForeignKey(MethodologyField)
    order = models.IntegerField(default=1)

    def __str__(self):
        return 'Option {} for {}'.format(self.title, self.field)

    class Meta(FieldOption.Meta):
        ordering = ['order']


class AssessmentTopic(models.Model):
    template = models.ForeignKey(AssessmentTemplate)
    title = models.CharField(max_length=255)
    order = models.IntegerField(default=1)

    def __str__(self):
        return '{} ({})'.format(self.title, self.template)

    class Meta:
        ordering = ['order']


class AffectedGroup(models.Model):
    template = models.ForeignKey(AssessmentTemplate)
    parent = models.ForeignKey('AffectedGroup',
                               default=None, null=True, blank=True)
    title = models.CharField(max_length=255)
    order = models.IntegerField(default=1)

    def __str__(self):
        return '{} ({})'.format(self.title, self.template)

    class Meta:
        ordering = ['order']


class Assessment(UserResource):
    """
    Assesssment belonging to a lead
    """
    lead = models.ForeignKey(Lead)
    meta_data = JSONField(default=None, blank=True, null=True)
    methodology_data = JSONField(default=None, blank=True, null=True)

    def __str__(self):
        return str(self.lead)
