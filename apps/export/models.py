from django.db import models
from django.core.cache import cache
from django.contrib.auth.models import User

from project.models import Project


class Export(models.Model):
    """
    Export model

    Represents an exported file along with few other attributes
    """

    PENDING = 'pending'
    STARTED = 'started'
    SUCCESS = 'success'
    FAILURE = 'failure'
    CANCELED = 'canceled'

    STATUS_CHOICES = (
        (PENDING, 'Pending'),
        (STARTED, 'Started'),
        (SUCCESS, 'Success'),
        (FAILURE, 'Failure'),
        (CANCELED, 'Canceled'),
    )

    XLSX = 'xlsx'
    DOCX = 'docx'
    PDF = 'pdf'
    JSON = 'json'

    FORMATS = (
        (XLSX, 'xlsx'),
        (DOCX, 'docx'),
        (PDF, 'pdf'),
        (JSON, 'json')
    )

    ENTRIES = 'entries'
    ASSESSMENTS = 'assessments'
    PLANNED_ASSESSMENTS = 'planned_assessments'

    DATA_TYPES = (
        (ENTRIES, 'Entries'),
        (ASSESSMENTS, 'Assessments'),
        (PLANNED_ASSESSMENTS, 'Planned Assessments'),
    )

    EXCEL = 'excel'
    REPORT = 'report'

    EXPORT_TYPES = (
        (EXCEL, 'Excel'),
        (REPORT, 'Report'),
        (JSON, 'Json'),
    )
    EXPORT_TASK_CACHE_KEY = 'EXPORT-{id}-TASK-ID'

    # Number of entries to proccess if is_preview is True
    PREVIEW_ENTRY_SIZE = 10
    PREVIEW_ASSESSMENT_SIZE = 10

    project = models.ForeignKey(Project, default=None, null=True, blank=True, on_delete=models.CASCADE)
    is_preview = models.BooleanField(default=False)

    title = models.CharField(max_length=255, blank=True)

    format = models.CharField(max_length=100, choices=FORMATS, blank=True)
    type = models.CharField(max_length=99, choices=DATA_TYPES, blank=True)
    export_type = models.CharField(max_length=100, choices=EXPORT_TYPES, blank=True)
    filters = models.JSONField(default=dict, blank=True, null=True,)

    mime_type = models.CharField(max_length=200, blank=True)
    file = models.FileField(upload_to='export/', max_length=255,
                            null=True, blank=True, default=None)
    exported_by = models.ForeignKey(User, on_delete=models.CASCADE)
    exported_at = models.DateTimeField(auto_now_add=True)

    pending = models.BooleanField(default=True)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default=PENDING)
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
        cache_key = self.EXPORT_TASK_CACHE_KEY.format(id=self.id)
        value = cache.get(cache_key)
        if clear:
            cache.delete(cache_key)
        return value

    def set_task_id(self, async_id):
        # Defined timeout is arbitrary now.
        return cache.set(self.EXPORT_TASK_CACHE_KEY.format(id=self.id), async_id, 345600)