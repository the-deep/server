from django.db import models
from django.contrib.auth.models import User

from project.models import Project


class Export(models.Model):
    """
    Export model

    Represents an exported file along with few other attributes
    """

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

    TYPES = (
        (ENTRIES, 'Entries'),
        (ASSESSMENTS, 'Assessments'),
    )

    project = models.ForeignKey(
        Project, default=None, null=True, blank=True, on_delete=models.CASCADE,
    )
    is_preview = models.BooleanField(default=False)

    title = models.CharField(max_length=255, blank=True)

    format = models.CharField(max_length=100, choices=FORMATS, blank=True)
    type = models.CharField(max_length=100, choices=TYPES, blank=True)

    mime_type = models.CharField(max_length=200, blank=True)
    file = models.FileField(upload_to='export/', max_length=255,
                            null=True, blank=True, default=None)
    exported_by = models.ForeignKey(User, on_delete=models.CASCADE)
    exported_at = models.DateTimeField(auto_now_add=True)

    pending = models.BooleanField(default=True)

    def __str__(self):
        return self.title

    @staticmethod
    def get_for(user):
        return Export.objects.filter(
            exported_by=user
        ).distinct()
