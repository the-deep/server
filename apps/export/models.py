from django.db import models
from django.core.cache import cache
from django.contrib.auth.models import User
from django.utils import timezone

from deep.caches import CacheKey
from deep.celery import app as celery_app
from project.models import Project
from export.mime_types import (
    DOCX_MIME_TYPE,
    PDF_MIME_TYPE,
    EXCEL_MIME_TYPE,
    JSON_MIME_TYPE,
)
from analysis.models import Analysis


class Export(models.Model):
    """
    Export model

    Represents an exported file along with few other attributes
    """
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        STARTED = 'started', 'Started'
        SUCCESS = 'success', 'Success'
        FAILURE = 'failure', 'Failure'
        CANCELED = 'canceled', 'Canceled'

    class DataType(models.TextChoices):
        ENTRIES = 'entries', 'Entries'
        ASSESSMENTS = 'assessments', 'Assessments'
        PLANNED_ASSESSMENTS = 'planned_assessments', 'Planned Assessments'
        ANALYSES = 'analyses', 'Analysis'

    class ExportType(models.TextChoices):
        EXCEL = 'excel', 'Excel'
        REPORT = 'report', 'Report'
        JSON = 'json', 'Json'

    class Format(models.TextChoices):
        XLSX = 'xlsx', 'xlsx'
        DOCX = 'docx', 'docx'
        PDF = 'pdf', 'pdf'
        JSON = 'json', 'json'

    # Used by extra options
    class StaticColumn(models.TextChoices):
        LEAD_PUBLISHED_ON = 'lead_published_on', 'Date of Source Publication'
        ENTRY_CREATED_BY = 'entry_created_by', 'Imported By'
        ENTRY_CREATED_AT = 'entry_created_at', 'Date Imported'
        ENTRY_CONTROL_STATUS = 'entry_control_status', 'Verification Status'
        LEAD_ID = 'lead_id', 'Source Id'
        LEAD_TITLE = 'lead_title', 'Source Title'
        LEAD_URL = 'lead_url', 'Source URL'
        LEAD_PAGE_COUNT = 'lead_page_count', 'Page Count'
        LEAD_ORGANIZATION_TYPE_AUTHOR = 'lead_organization_type_author', 'Authoring Organizations Type'
        LEAD_ORGANIZATION_AUTHOR = 'lead_organization_author', 'Author'
        LEAD_ORGANIZATION_SOURCE = 'lead_organization_source', 'Publisher'
        LEAD_PRIORITY = 'lead_priority', 'Source Priority'
        LEAD_ASSIGNEE = 'lead_assignee', 'Assignee'
        ENTRY_ID = 'entry_id', 'Entry Id'
        LEAD_ENTRY_ID = 'lead_entry_id', 'Source-Entry Id'
        ENTRY_EXCERPT = 'entry_excerpt', 'Modified Excerpt, Original Excerpt'

    MIME_TYPE_MAP = {
        Format.XLSX: EXCEL_MIME_TYPE,
        Format.DOCX: DOCX_MIME_TYPE,
        Format.PDF: PDF_MIME_TYPE,
        Format.JSON: JSON_MIME_TYPE,
    }
    DEFAULT_MIME_TYPE = 'application/octet-stream'

    DEFAULT_TITLE_LABEL = {
        (DataType.ENTRIES, ExportType.EXCEL, Format.XLSX): 'Entries Excel Export',
        (DataType.ENTRIES, ExportType.REPORT, Format.DOCX): 'Entries General Export',
        (DataType.ENTRIES, ExportType.REPORT, Format.PDF): 'Entries General Export',
        (DataType.ENTRIES, ExportType.JSON, Format.JSON): 'Entries JSON Export',
        (DataType.ASSESSMENTS, ExportType.EXCEL, Format.XLSX): 'Assessments Excel Export',
        (DataType.ASSESSMENTS, ExportType.JSON, Format.JSON): 'Assessments JSON Export',
        (DataType.PLANNED_ASSESSMENTS, ExportType.EXCEL, Format.XLSX): 'Planned Assessments Excel Export',
        (DataType.PLANNED_ASSESSMENTS, ExportType.JSON, Format.JSON): 'Planned Assessments JSON Export',
        (DataType.ANALYSES, ExportType.EXCEL, Format.XLSX): 'Analysis Excel Export',
    }

    # Number of entries to proccess if is_preview is True
    PREVIEW_ENTRY_SIZE = 10
    PREVIEW_ASSESSMENT_SIZE = 10

    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    is_preview = models.BooleanField(default=False)

    title = models.CharField(max_length=255)

    format = models.CharField(max_length=100, choices=Format.choices)
    type = models.CharField(max_length=99, choices=DataType.choices)
    export_type = models.CharField(max_length=100, choices=ExportType.choices)
    exported_by = models.ForeignKey(User, on_delete=models.CASCADE)
    exported_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    ended_at = models.DateTimeField(null=True, blank=True)

    # Lead filters
    filters = models.JSONField(default=dict)
    # Additional configuration options
    extra_options = models.JSONField(default=dict)

    mime_type = models.CharField(max_length=200, blank=True)
    file = models.FileField(upload_to='export/', max_length=255, null=True, blank=True, default=None)

    pending = models.BooleanField(default=True)
    status = models.CharField(max_length=30, choices=Status.choices, default=Status.PENDING)
    is_deleted = models.BooleanField(default=False)
    is_archived = models.BooleanField(default=False)

    # used for analysis export
    analysis = models.ForeignKey(
        Analysis, null=True, blank=True,
        verbose_name="analysis",
        on_delete=models.SET_NULL,
    )

    def __str__(self):
        return self.title

    @staticmethod
    def get_for(user):
        return Export.objects.filter(
            exported_by=user,
            is_deleted=False
        ).distinct()

    @classmethod
    def generate_title(cls, data_type, export_type, export_format):
        file_label = cls.DEFAULT_TITLE_LABEL[(data_type, export_type, export_format)]
        time_str = timezone.now().strftime('%Y%m%d')
        return f'{time_str} DEEP {file_label}'

    def get_task_id(self, clear=False):
        cache_key = CacheKey.EXPORT_TASK_CACHE_KEY_FORMAT.format(self.pk)
        value = cache.get(cache_key)
        if clear:
            cache.delete(cache_key)
        return value

    def cancle(self, commit=True):
        if self.status not in [Export.Status.PENDING, Export.Status.STARTED]:
            return
        celery_app.control.revoke(self.get_task_id(clear=True), terminate=True)
        self.status = Export.Status.CANCELED
        if commit:
            self.save(update_fields=('status',))

    def save(self, *args, **kwargs):
        self.title = self.title or self.generate_title(self.type, self.export_type, self.format)
        return super().save(*args, **kwargs)

    def set_task_id(self, async_id):
        # Defined timeout is arbitrary now.
        return cache.set(CacheKey.EXPORT_TASK_CACHE_KEY_FORMAT.format(self.pk), async_id, 345600)
