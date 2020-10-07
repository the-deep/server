from django.db import models
from user_resource.models import UserResource


class OrganizationType(models.Model):
    title = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)
    relief_web_id = models.IntegerField(unique=True, blank=True, null=True)

    def __str__(self):
        return self.title


class Organization(UserResource):
    parent = models.ForeignKey(
        # TODO: should we do this ? on_delete=models.CASCADE
        'Organization', on_delete=models.CASCADE,
        null=True, blank=True,
        help_text='Deep will use the parent organization data instead of current',
        related_name='related_childs',
    )

    title = models.CharField(max_length=255)
    short_name = models.CharField(max_length=255, blank=True)
    long_name = models.CharField(max_length=512, blank=True)
    url = models.CharField(max_length=255, blank=True)
    # Organizations pulled from reliefweb
    relief_web_id = models.IntegerField(unique=True, blank=True, null=True)

    logo = models.ForeignKey(
        'gallery.File',
        on_delete=models.SET_NULL,
        null=True, blank=True, default=None,
    )

    regions = models.ManyToManyField('geo.Region', blank=True)

    organization_type = models.ForeignKey(
        OrganizationType,
        on_delete=models.SET_NULL,
        null=True, blank=True, default=None,
    )

    verified = models.BooleanField(default=False)
    client_id = None

    class Meta:
        # Admin panel permissions
        permissions = (
            ("can_merge", "Can Merge organizations"),
        )

    @property
    def data(self):
        """
        Get merged organization if merged
        """
        if hasattr(self, '_data'):
            return self._data

        if self.parent_id:
            self._data = self.parent
        else:
            self._data = self
        return self._data

    def __str__(self):
        return f'{self.pk} : ({self.short_name}) {self.title} ' + (
            '(MERGED)' if self.parent else ''
        )
