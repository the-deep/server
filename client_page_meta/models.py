from django.db import models


class Page(models.Model):
    title = models.CharField(max_length=300)
    page_id = models.CharField(max_length=300, unique=True)
    help_url = models.TextField(blank=True)

    def __str__(self):
        return '{} {}'.format(self.title, self.page_id)
