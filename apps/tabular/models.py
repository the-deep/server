import time

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
    ODS = 'ods'

    FILE_TYPES = (
        (CSV, 'CSV'),
        (XLSX, 'XLSX'),
        (ODS, 'ODS'),
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
        File, null=True, blank=True, on_delete=models.SET_NULL,
    )
    project = models.ForeignKey(
        Project, null=True, default=None, on_delete=models.CASCADE,
    )
    url = models.TextField(null=True, blank=True)
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

    def get_pending_fields_id(self):
        return Field.objects.filter(
            sheet__book=self,
            cache__status=Field.CACHE_PENDING,
        ).distinct().values_list('id', flat=True)

    def get_status(self):
        return Field.objects.filter(
            sheet__book=self,
            cache__status=Field.CACHE_PENDING,
        ).count() == 0

    def get_processed_fields(self, fields=[]):
        """
        Return success cached fields
        """
        return Field.objects.filter(
            sheet__book=self, cache__status=Field.CACHE_SUCCESS, id__in=fields,
        ).distinct()

    def __str__(self):
        return self.title


class Sheet(models.Model):
    title = models.CharField(max_length=255)
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    data_row_index = models.IntegerField(default=1)
    options = JSONField(default=None, blank=True, null=True)
    hidden = models.BooleanField(default=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.current_data_row_index = self.data_row_index

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        # Re-Trigger column generation if data_row_index changed
        if self.data_row_index != self.current_data_row_index:
            from tabular.tasks import tabular_generate_columns_image  # to prevent circular import
            # First set cache pending to all fields
            for field in self.field_set.all():
                field.cache['status'] = Field.CACHE_PENDING
                field.cache['time'] = time.time()
                field.save()
            field_ids = self.field_set.values_list('id', flat=True)
            tabular_generate_columns_image.delay(list(field_ids))

        # Update current_options value
        self.current_data_row_index = self.current_data_row_index


class Field(models.Model):
    CACHE_PENDING = 'pending'
    CACHE_SUCCESS = 'success'
    CACHE_ERROR = 'error'

    NUMBER = 'number'
    STRING = 'string'
    DATETIME = 'datetime'
    GEO = 'geo'

    CACHE_STATUS_TYPES = (
        (CACHE_PENDING, 'Pending'),
        (CACHE_SUCCESS, 'Success'),
        (CACHE_ERROR, 'Error'),
    )
    FIELD_TYPES = (
        (NUMBER, 'Number'),
        (STRING, 'String'),
        (DATETIME, 'Datetime'),
        (GEO, 'Geo'),
    )

    title = models.CharField(max_length=255)
    sheet = models.ForeignKey(Sheet, on_delete=models.CASCADE)
    type = models.CharField(
        max_length=30,
        choices=FIELD_TYPES,
        default=STRING
    )
    hidden = models.BooleanField(default=False)
    options = JSONField(default=None, blank=True, null=True)
    cache = JSONField(default=dict, blank=True, null=True)
    ordering = models.IntegerField(default=1)
    data = JSONField(default=list)

    @property
    def actual_data(self):
        row_index = self.sheet.data_row_index
        return self.data[row_index:]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.current_type = self.type
        self.current_options = self.options

    def __str__(self):
        return self.title

    def cast_data(self, geos_names={}, geos_codes={}):
        """
        Returns processed, invalid and empty values corresponding to the fields
        after trying to cast
        """
        type = self.type
        options = self.options

        cast_func = get_cast_function(type, geos_names, geos_codes)

        values = self.data
        regions = {}

        # Now iterate through every item to find empty/invalid values
        for i, value in enumerate(values):
            val = value['value']

            value.pop('invalid', None)
            value.pop('empty', None)
            value.pop('processed_value', None)

            if val is None or val == '':
                value['empty'] = True
                continue
            casted = cast_func(val, **self.options)

            if casted is None:
                value['invalid'] = True
            elif type == Field.GEO:
                value['processed_value'] = casted['id']
                regions[casted['region']] = casted['region_title']
            elif type == Field.NUMBER:
                value['processed_value'] = casted[0]  # (number, separator)
            elif type == Field.DATETIME:
                value['processed_value'] = casted.isoformat()  # (parsed_date)

        if type == Field.GEO and regions:
            options['regions'] = [
                {'id': k, 'title': v} for k, v in regions.items()
            ]

        return {
            'values': values,
            'options': options
        }

    def save(self, *args, **kwargs):
        if hasattr(self, 'geodata'):
            self.geodata.delete()
        super().save(*args, **kwargs)
        self.current_type = self.type
        self.current_options = self.options

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
