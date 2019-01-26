# Some useful abstract models

from django.db import models
from django.contrib.postgres.fields import JSONField


class Field(models.Model):
    title = models.CharField(max_length=255)
    is_required = models.BooleanField(default=True)

    # Fields
    STRING = 'string'
    NUMBER = 'number'
    DATE = 'date'
    DATERANGE = 'daterange'
    SELECT = 'select'
    MULTISELECT = 'multiselect'

    FIELD_TYPES = (
        (STRING, 'String'),
        (NUMBER, 'Number'),
        (DATE, 'Date'),
        (DATERANGE, 'Date Range'),
        (SELECT, 'Select'),
        (MULTISELECT, 'Multiselect'),
    )

    # Sources
    COUNTRIES = 'countries'
    ORGANIZATIONS = 'organizations'
    DONORS = 'donors'

    SOURCE_TYPES = (
        (COUNTRIES, 'Countries'),
        (ORGANIZATIONS, 'Organizations'),
        (DONORS, 'Donors'),
    )

    field_type = models.CharField(
        max_length=50,
        choices=FIELD_TYPES,
        default=STRING,
    )

    source_type = models.CharField(
        max_length=50,
        choices=SOURCE_TYPES,
        null=True, blank=True,
        default=None,
    )

    properties = JSONField(default=None, blank=True, null=True)

    class Meta:
        abstract = True

    def get_options(self):
        if self.source_type in [type[0] for type in Field.SOURCE_TYPES]:
            return []
        return [{'key': x.key, 'title': x.title} for x in self.options.all()]

    def get_value(self, raw_value):
        value = raw_value
        options = {x['key']: x['title'] for x in self.get_options()}
        if self.field_type == Field.SELECT:
            value = options.get(raw_value, raw_value)
        elif self.field_type == Field.MULTISELECT:
            value = [options.get(x, x) for x in raw_value]
        # TODO: for other types
        return value


class FieldOption(models.Model):
    key = models.CharField(max_length=255)
    title = models.CharField(max_length=255)

    class Meta:
        abstract = True
