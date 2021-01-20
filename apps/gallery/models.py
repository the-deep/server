import uuid as python_uuid
from django.contrib.postgres.fields import JSONField, ArrayField
from django.db import models
from django.conf import settings
from django.urls import reverse
from user_resource.models import UserResource


class File(UserResource):
    uuid = models.UUIDField(default=python_uuid.uuid4, editable=False, unique=True)
    title = models.CharField(max_length=255)

    file = models.FileField(upload_to='gallery/', max_length=255,
                            null=True, blank=True, default=None)
    mime_type = models.CharField(max_length=130, blank=True, null=True)
    metadata = JSONField(default=None, blank=True, null=True)

    is_public = models.BooleanField(default=False)
    projects = models.ManyToManyField('project.Project', blank=True)

    def __str__(self):
        return self.title

    @property
    def url(self):
        if self.file:
            return self.file.url

    @staticmethod
    def get_for(user):
        return File.objects.filter(created_by=user)

    def can_get(self, user):
        return True
        # return self in File.get_for(user)

    def get_file_url(self):
        return '{protocol}://{domain}{url}'.format(
            protocol=settings.HTTP_PROTOCOL,
            domain=settings.DJANGO_API_HOST,
            url=reverse(
                'gallery_private_url',
                kwargs={'uuid': self.uuid, 'filename': self.title},
            )
        )

    def can_modify(self, user):
        return self.created_by == user


class FilePreview(models.Model):
    file_ids = ArrayField(models.IntegerField())
    text = models.TextField(blank=True)
    ngrams = JSONField(null=True, blank=True, default=None)
    extracted = models.BooleanField(default=False)

    def __str__(self):
        return 'Text extracted for {}'.format(self.file)
