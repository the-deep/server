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
    COUNTRIES = 'countries'
    ORGANIZATIONS = 'organizations'

    FIELD_TYPES = (
        (STRING, 'String'),
        (NUMBER, 'Number'),
        (DATE, 'Date'),
        (SELECT, 'Select'),
        (MULTISELECT, 'Multiselect'),
        (COUNTRIES, 'Countries'),
        (ORGANIZATIONS, 'Organizations'),
    )

    field_type = models.CharField(
        max_length=50,
        choices=FIELD_TYPES,
        default=STRING,
    )

    properties = JSONField(default=None, blank=True, null=True)

    class Meta:
        abstract = True

    def get_type(self):
        if self.field_type == Field.COUNTRIES or \
                self.field_type == Field.ORGANIZATIONS:
            return Field.SELECT

        return self.field_type

    def get_options(self):
        from geo.models import Region
        from organization.models import Organization

        if self.field_type == Field.COUNTRIES:
            countries = Region.objects.filter(public=True)
            return [
                {
                    'key': country.id,
                    'title': country.title,
                } for country in countries
            ]

        if self.field_type == Field.ORGANIZATIONS:
            organizations = Organization.objects.all()
            return [
                {
                    'key': org.id,
                    'title': org.title,
                } for org in organizations
            ]

        return self.options


class FieldOption(models.Model):
    key = models.CharField(max_length=255)
    title = models.CharField(max_length=255)

    class Meta:
        abstract = True
