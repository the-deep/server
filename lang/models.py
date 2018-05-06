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


class Link(models.Model):
    language = models.CharField(
        max_length=255,
        choices=settings.LANGUAGES,
        default=settings.LANGUAGE_CODE,
    )
    key = models.CharField(max_length=255)
    string = models.ForeignKey(String)

    def __str__(self):
        return '{} : {} ({})'.format(self.key, self.string.value,
                                     self.language)
