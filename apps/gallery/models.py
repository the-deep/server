from django.contrib.postgres.fields import JSONField, ArrayField
from django.db import models
from user_resource.models import UserResource


class File(UserResource):
    title = models.CharField(max_length=255)

    file = models.FileField(upload_to='gallery/', max_length=255,
                            null=True, blank=True, default=None)
    mime_type = models.CharField(max_length=130, blank=True, null=True)
    metadata = JSONField(default=None, blank=True, null=True)

    is_public = models.BooleanField(default=True)
    projects = models.ManyToManyField('project.Project', blank=True)

    def __str__(self):
        return self.title

    @staticmethod
    def get_for(user):
        return File.objects.all()
        # return File.objects.filter(
        #     models.Q(created_by=user) |
        #     models.Q(is_public=True) |
        #     models.Q(permitted_users=user) |
        #     models.Q(permitted_user_groups__members=user)
        # ).distinct()

    def can_get(self, user):
        return True
        # return self in File.get_for(user)

    def can_modify(self, user):
        return self.created_by == user


class FilePreview(models.Model):
    file_ids = ArrayField(models.IntegerField())
    text = models.TextField(blank=True)
    ngrams = JSONField(null=True, blank=True, default=None)
    extracted = models.BooleanField(default=False)

    def __str__(self):
        return 'Text extracted for {}'.format(self.file)
