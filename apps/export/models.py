from django.db import models
from django.core.cache import cache
from django.contrib.auth.models import User

from deep.caches import CacheKey
from project.models import Project


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

    class Format(models.TextChoices):
        XLSX = 'xlsx', 'xlsx'
        DOCX = 'docx', 'docx'
        PDF = 'pdf', 'pdf'
        JSON = 'json', 'json'

    class DataType(models.TextChoices):
        ENTRIES = 'entries', 'Entries'
        ASSESSMENTS = 'assessments', 'Assessments'
        PLANNED_ASSESSMENTS = 'planned_assessments', 'Planned Assessments'

    class ExportType(models.TextChoices):
        EXCEL = 'excel', 'Excel'
        REPORT = 'report', 'Report'
        JSON = 'json', 'Json'

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

    def __str__(self):
        return self.title

    @staticmethod
    def get_for(user):
        return Export.objects.filter(
            exported_by=user,
            is_deleted=False
        ).distinct()

    def get_task_id(self, clear=False):
        cache_key = CacheKey.EXPORT_TASK_CACHE_KEY_FORMAT.format(self.pk)
        value = cache.get(cache_key)
        if clear:
            cache.delete(cache_key)
        return value

    def set_task_id(self, async_id):
        # Defined timeout is arbitrary now.
        return cache.set(CacheKey.EXPORT_TASK_CACHE_KEY_FORMAT.format(self.pk), async_id, 345600)
