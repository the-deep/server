from django.db import models
from django.contrib.postgres.fields import JSONField
from user_resource.models import UserResource


class Region(UserResource):
    """
    Region model

    Represents mostly country but can also be any other region.
    Region can be global in which case it will be available directly
    to public. Project specific regions won't be available publicly.
    """
    code = models.CharField(max_length=10)
    title = models.CharField(max_length=255)
    public = models.BooleanField(default=True)

    key_figures = JSONField(default=None, blank=True, null=True)
    regional_groups = JSONField(default=None, blank=True, null=True)
    population_data = JSONField(default=None, blank=True, null=True)
    media_sources = JSONField(default=None, blank=True, null=True)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['title', 'code']

    def get_verbose_title(self):
        if self.public:
            return self.title
        return '{} (Private)'.format(self.title)

    def clone_to_private(self, user):
        region = Region(
            code=self.code,
            title=self.title,
            public=False,
            regional_groups=self.regional_groups,
            key_figures=self.key_figures,
            population_data=self.population_data,
            media_sources=self.media_sources,
        )

        root_level = AdminLevel.objects.filter(
            region=self,
            parent=None,
        ).first()

        parent = None
        admin_level = root_level
        while admin_level:
            parent = admin_level.clone_to(self, parent)

        region.created_by = user
        region.modified_by = user

        region.save()
        return region

    @staticmethod
    def get_for(user):
        return Region.objects.filter(
            models.Q(public=True) |
            models.Q(created_by=user) |
            models.Q(project__members=user)
        ).distinct()

    def can_get(self, user):
        return self in Region.get_for(user)

    def can_modify(self, user):
        return (user.is_superuser and self.public) or (
            self.created_by == user
        )


class AdminLevel(models.Model):
    """
    A region can contain multiple admin levels.

    Admin level data is in the form of geojson.

    Note that to auto generate geo areas from geojson
    we need (at least some of) the following attributes:

    * name_prop -   Property defining name of geo area
    * code_prop -   Property defining code of geo area

    To also auto link parent geo areas:

    * parent_name_prop  -   Property defining name of parent of the geo area
    * parent_code_prop  -   Property defining code of parent of the geo area
    """
    region = models.ForeignKey(Region, on_delete=models.CASCADE)
    parent = models.ForeignKey('AdminLevel',
                               on_delete=models.SET_NULL,
                               null=True, blank=True, default=None)
    title = models.CharField(max_length=255)
    name_prop = models.CharField(max_length=255, blank=True)
    code_prop = models.CharField(max_length=255, blank=True)
    parent_name_prop = models.CharField(max_length=255, blank=True)
    parent_code_prop = models.CharField(max_length=255, blank=True)

    geo_shape = JSONField(default=None, blank=True, null=True)

    def __str__(self):
        return self.title

    def clone_to(self, region, parent):
        admin_level = AdminLevel(
            region=region,
            parent=parent,
            title=self.title,
            name_prop=self.name_prop,
            code_prop=self.code_prop,
            parent_name_prop=self.parent_name_prop,
            parent_code_prop=self.parent_code_prop,
            geo_shape=self.geo_shape,
        )

        root_area = GeoArea.objects.filter(
            admin_level=self,
            parent=None,
        ).first()

        parent = None
        area = root_area
        while area:
            parent = area.clone_to(self, parent)

        admin_level.save()
        return admin_level

    # Admin level permissions are same as region permissions

    @staticmethod
    def get_for(user):
        return AdminLevel.objects.filter(
            models.Q(region__public=True) |
            models.Q(region__created_by=user) |
            models.Q(region__project__members=user)
        ).distinct()

    def can_get(self, user):
        return self.region.can_get(user)

    def can_modify(self, user):
        return self.region.can_modify(user)


class GeoArea(models.Model):
    """
    An actual geo area in a given admin level
    """
    admin_level = models.ForeignKey(AdminLevel, on_delete=models.CASCADE)
    parent = models.ForeignKey('GeoArea',
                               on_delete=models.SET_NULL,
                               null=True, blank=True, default=None)
    title = models.CharField(max_length=255)
    code = models.CharField(max_length=255, blank=True)
    data = JSONField(default=None, blank=True, null=True)

    def __str__(self):
        return self.title

    def clone_to(self, admin_level, parent):
        geo_area = GeoArea(
            admin_level=admin_level,
            parent=parent,
            title=self.title,
            code=self.code,
            data=self.data
        )
        geo_area.save()
        return geo_area

    # Permissions are same as region
    @staticmethod
    def get_for(user):
        return AdminLevel.objects.filter(
            models.Q(admin_level__region__public=True) |
            models.Q(admin_level__region__created_by=user) |
            models.Q(admin_level__region__project__members=user)
        ).distinct()

    def can_get(self, user):
        return self.admin_level.can_get(user)

    def can_modify(self, user):
        return self.admin_level.can_modify(user)
