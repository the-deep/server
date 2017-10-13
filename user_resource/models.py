from django.db import models
from django.contrib.auth.models import User


class UserResource(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User,
                                   related_name='%(class)s_created',
                                   default=None, blank=True, null=True,
                                   on_delete=models.SET_NULL)
    modified_by = models.ForeignKey(User,
                                    related_name='%(class)s_modified',
                                    default=None, blank=True, null=True,
                                    on_delete=models.SET_NULL)

    class Meta:
        abstract = True
        ordering = ['-modified_at', '-created_at']
