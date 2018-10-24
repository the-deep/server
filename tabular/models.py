from django.db import models
from django.contrib.postgres.fields import JSONField, ArrayField, HStoreField
from user_resource.models import UserResource
from gallery.models import File


class Book(UserResource):
    # FILE TYPES
    CSV = 'csv'
    XLSX = 'xlsx'

    # ERROR TYPES
    UNKNOWN_ERROR = 100
    FILE_TYPE_ERROR = 101

    FILE_TYPES = (
        (CSV, 'CSV'),
        (XLSX, 'XLSX'),
    )

    ERROR_TYPES = (
        (UNKNOWN_ERROR, 'Unknown error'),
        (FILE_TYPE_ERROR, 'File type error'),
    )

    title = models.CharField(max_length=255)
    file = models.OneToOneField(File, null=True, blank=True)
    url = models.TextField(null=True, blank=True)
    pending = models.BooleanField(default=True)
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

    def __str__(self):
        return self.title


class Sheet(models.Model):
    title = models.CharField(max_length=255)
    book = models.ForeignKey(Book)
    options = JSONField(default=None, blank=True, null=True)
    data = ArrayField(HStoreField(), default=list)

    def __str__(self):
        return self.title


class Field(models.Model):
    NUMBER = 'number'
    STRING = 'string'

    FIELD_TYPES = (
        (NUMBER, 'Number'),
        (STRING, 'String'),
    )

    label = models.CharField(max_length=255)
    sheet = models.ForeignKey(Sheet)
    type = models.CharField(
        max_length=30,
        choices=FIELD_TYPES,
        default=STRING
    )
    options = JSONField(default=None, blank=True, null=True)

    def __str__(self):
        return self.label
