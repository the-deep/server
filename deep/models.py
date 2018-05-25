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
    DONORS = 'donors'

    FIELD_TYPES = (
        (STRING, 'String'),
        (NUMBER, 'Number'),
        (DATE, 'Date'),
        (SELECT, 'Select'),
        (MULTISELECT, 'Multiselect'),
        (COUNTRIES, 'Countries'),
        (ORGANIZATIONS, 'Organizations'),
        (DONORS, 'Donors'),
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
                self.field_type == Field.ORGANIZATIONS or \
                self.field_type == Field.DONORS:
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

        if self.field_type == Field.DONORS:
            donors = Organization.objects.filter(donor=True)
            return [
                {
                    'key': org.id,
                    'title': org.title,
                } for org in donors
            ]

        return [{'key': x.key, 'title': x.title} for x in self.options.all()]

    def get_value(self, raw_value):
        value = raw_value
        options = {x['key']: x['title'] for x in self.get_options()}
        if self.field_type in (
                Field.SELECT, Field.ORGANIZATIONS,
                Field.COUNTRIES, Field.DONORS):
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
