# Some useful abstract models

from django.db import models
from django.contrib.postgres.fields import JSONField


class Field(models.Model):
    title = models.CharField(max_length=255)

    STRING = 'string'
    NUMBER = 'number'
    DATE = 'date'
    SELECT = 'select'
    MULTISELECT = 'multiselect'

    FIELD_TYPES = (
        (STRING, 'String'),
        (NUMBER, 'Number'),
        (DATE, 'Date'),
        (SELECT, 'Select'),
        (MULTISELECT, 'Multiselect')
    )

    field_type = models.CharField(
        max_length=50,
        choices=FIELD_TYPES,
        default=STRING,
    )

    properties = JSONField(default=None, blank=True, null=True)

    class Meta:
        abstract = True


class FieldOption(models.Model):
    key = models.CharField(max_length=255)
    title = models.CharField(max_length=255)

    class Meta:
        abstract = True
