from django.db import models
from django.contrib.postgres.fields import JSONField

from user_resource.models import UserResource
from lead.models import Lead


class AssessmentTemplate(UserResource):
    title = models.CharField(max_length=255)

    def __str__(self):
        return self.title


class MetadataGroup(models.Model):
    template = models.ForeignKey(AssessmentTemplate)
    title = models.CharField(max_length=255)

    def __str__(self):
        return '{} ({})'.format(self.title, self.template)


class MetadataField(models.Model):
    group = models.ForeignKey(MetadataGroup)
    title = models.CharField(max_length=255)

    STRING = 'string'
    NUMBER = 'number'
    DATE = 'date'

    FIELD_TYPES = (
        (STRING, 'String'),
        (NUMBER, 'Number'),
        (DATE, 'Date'),
    )

    field_type = models.CharField(
        max_length=50,
        choices=FIELD_TYPES,
        default=STRING,
    )

    properties = JSONField(default=None, blank=True, null=True)

    def __str__(self):
        return '{} ({})'.format(self.title, self.group.template)


class MetadataOptions(models.Model):
    field = models.ForeignKey(MetadataField)
    key = models.CharField(max_length=255)
    title = models.CharField(max_length=255)

    def __str__(self):
        return 'Option {} for {}'.format(self.title, self.field)


class Assessment(UserResource):
    """
    Assesssment belonging to a lead
    """
    lead = models.ForeignKey(Lead)
    meta_data = JSONField(default=None, blank=True, null=True)

    def __str__(self):
        return str(self.lead)
