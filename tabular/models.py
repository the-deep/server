from django.db import models
from django.contrib.postgres.fields import JSONField
from user_resource.models import UserResource
from gallery.models import File
from project.models import Project
from utils.common import get_file_from_url

from tabular.utils import get_cast_function


class Book(UserResource):
    # STATUS TYPES
    INITIAL = 'initial'
    PENDING = 'pending'
    SUCCESS = 'success'
    FAILED = 'failed'

    STATUS_TYPES = (
        (INITIAL, 'Initial (Book Just Added)'),
        (PENDING, 'Pending'),
        (SUCCESS, 'Success'),
        (FAILED, 'Failed'),
    )

    # FILE TYPES
    CSV = 'csv'
    XLSX = 'xlsx'

    FILE_TYPES = (
        (CSV, 'CSV'),
        (XLSX, 'XLSX'),
    )

    META_REQUIRED_FILE_TYPES = [XLSX]

    # ERROR TYPES
    UNKNOWN_ERROR = 100
    FILE_TYPE_ERROR = 101

    ERROR_TYPES = (
        (UNKNOWN_ERROR, 'Unknown error'),
        (FILE_TYPE_ERROR, 'File type error'),
    )

    title = models.CharField(max_length=255)
    file = models.OneToOneField(
        File, null=True, blank=True, on_delete=models.SET_NULL)
    project = models.ForeignKey(Project, null=True, default=None)
    url = models.TextField(null=True, blank=True)
    meta_status = models.CharField(
        max_length=30,
        choices=STATUS_TYPES,
        default=INITIAL,
    )
    status = models.CharField(
        max_length=30,
        choices=STATUS_TYPES,
        default=INITIAL,
    )
    error = models.CharField(
        max_length=30,
        choices=ERROR_TYPES,
        blank=True, null=True,
    )
    file_type = models.CharField(
        max_length=30,
        choices=FILE_TYPES,
    )
    options = JSONField(default=None, blank=True, null=True)
    meta = JSONField(default=None, blank=True, null=True)

    def get_file(self):
        if self.file:
            return self.file.file
        elif self.url:
            return get_file_from_url(self.url)

    def __str__(self):
        return self.title


class Sheet(models.Model):
    title = models.CharField(max_length=255)
    book = models.ForeignKey(Book)
    options = JSONField(default=None, blank=True, null=True)
    data = JSONField(default={})
    hidden = models.BooleanField(default=False)

    def cast_data_to(self, field, geos_names={}, geos_codes={}):
        """
        Returns processed, invalid and empty values corresponding to the fields
        after trying to cast
        """
        type = field.type
        options = field.options

        cast_func = get_cast_function(type, geos_names, geos_codes)

        values = self.data.get('columns', {}).get(str(field.id), [])

        # Now iterate through every item to find empty/invalid values
        for i, value in enumerate(values):
            val = value['value']
            if val is None or val == '':
                value['empty'] = True
                value['invalid'] = False
                continue
            casted = cast_func(val, **field.options)
            if casted is None:
                value['invalid'] = True
                value['empty'] = False
            else:
                value['invalid'] = False
                value['empty'] = False
                if type == Field.GEO:
                    value['processed_value'] = casted['id']
                    options['region'] = casted['region']

        return {
            'values': values,
            'options': options
        }

    def __str__(self):
        return self.title


class Field(models.Model):
    NUMBER = 'number'
    STRING = 'string'
    DATETIME = 'datetime'
    GEO = 'geo'

    FIELD_TYPES = (
        (NUMBER, 'Number'),
        (STRING, 'String'),
        (DATETIME, 'Datetime'),
        (GEO, 'Geo'),
    )

    title = models.CharField(max_length=255)
    sheet = models.ForeignKey(Sheet)
    type = models.CharField(
        max_length=30,
        choices=FIELD_TYPES,
        default=STRING
    )
    hidden = models.BooleanField(default=False)
    options = JSONField(default=None, blank=True, null=True)
    ordering = models.IntegerField(default=1)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.current_type = self.type

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if hasattr(self, 'geodata'):
            self.geodata.delete()
        super().save(*args, **kwargs)
        self.current_type = self.type

    def get_option(self, key, default_value=None):
        options = self.options or {}
        return options.get(key, default_value)

    class Meta:
        ordering = ['ordering']


class Geodata(models.Model):
    # STATUS TYPES
    PENDING = 'pending'
    SUCCESS = 'success'
    FAILED = 'failed'

    STATUS_TYPES = (
        (PENDING, 'Pending'),
        (SUCCESS, 'Success'),
        (FAILED, 'Failed'),
    )

    data = JSONField(default=None, blank=True, null=True)
    field = models.OneToOneField(
        Field,
        on_delete=models.CASCADE,
        related_name='geodata'
    )
    status = models.CharField(
        max_length=30,
        choices=STATUS_TYPES,
        default=PENDING,
    )

    def __str__(self):
        return '{} (Geodata)'.format(self.field.title)
