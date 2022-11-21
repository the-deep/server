from django.db import models
from deep.middleware import get_current_user
from user_resource.models import UserResource


class OrganizationType(models.Model):
    title = models.CharField(max_length=255, blank=True)
    short_name = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField(blank=True)
    relief_web_id = models.IntegerField(unique=True, blank=True, null=True)

    def __str__(self):
        return self.title


class Organization(UserResource):
    class SourceType(models.IntegerChoices):
        WEB_INFO_EXTRACT_VIEW = 0, 'Web info extract VIEW'
        WEB_INFO_DATA_VIEW = 1, 'Web Info Data VIEW'
        CONNECTOR = 2, 'Connector'

    parent = models.ForeignKey(
        # TODO: should we do this ? on_delete=models.CASCADE
        'Organization', on_delete=models.CASCADE,
        null=True, blank=True,
        help_text='Deep will use the parent organization data instead of current',
        related_name='related_childs',
    )

    source = models.PositiveSmallIntegerField(choices=SourceType.choices, null=True, blank=True)
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
    popularity = models.IntegerField(default=0)  # Holds total number of used within the deep

    class Meta:
        # Admin panel permissions
        permissions = (
            ("can_merge", "Can Merge organizations"),
        )

    def __str__(self):
        return f'{self.pk} : ({self.short_name}) {self.title} ' + (
            '(MERGED)' if self.parent else ''
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

    def save(self, *args, **kwargs):
        current_user = get_current_user()
        if current_user:
            if self.pk is None:
                self.created_by = current_user
            self.modified_by = current_user
        super().save(*args, **kwargs)

    def get_organization_type_display(self):
        return self.data.organization_type.title
