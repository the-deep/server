from django.db import models
from django.conf import settings


class String(models.Model):
    language = models.CharField(
        max_length=255,
        choices=settings.LANGUAGES,
        default=settings.LANGUAGE_CODE,
    )
    value = models.TextField()

    def __str__(self):
        return '{} ({})'.format(self.value, self.language)


class LinkCollection(models.Model):
    key = models.CharField(max_length=255)

    def __str__(self):
        return self.key


class Link(models.Model):
    language = models.CharField(
        max_length=255,
        choices=settings.LANGUAGES,
        default=settings.LANGUAGE_CODE,
    )
    link_collection = models.ForeignKey(LinkCollection,
                                        related_name='links')
    key = models.CharField(max_length=255)
    string = models.ForeignKey(String,
                               null=True, blank=True, default=None,
                               on_delete=models.SET_NULL)

    def __str__(self):
        return '{} : {} ({})'.format(self.key, self.string.value,
                                     self.language)
