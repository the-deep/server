from django.contrib.gis.db import models
from django.contrib.postgres.fields import JSONField
from user_resource.models import UserResource
from gallery.models import File


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

    regional_groups = JSONField(default=None, blank=True, null=True)
    key_figures = JSONField(default=None, blank=True, null=True)
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
            title='{} (cloned)'.format(self.title),
            public=False,
            regional_groups=self.regional_groups,
            key_figures=self.key_figures,
            population_data=self.population_data,
            media_sources=self.media_sources,
        )

        region.created_by = user
        region.modified_by = user
        region.save()

        root_levels = AdminLevel.objects.filter(
            region=self,
            parent=None,
        ).distinct()

        for root_level in root_levels:
            root_level.clone_to(region)

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
    level = models.IntegerField(null=True, blank=True, default=None)
    name_prop = models.CharField(max_length=255, blank=True)
    code_prop = models.CharField(max_length=255, blank=True)
    parent_name_prop = models.CharField(max_length=255, blank=True)
    parent_code_prop = models.CharField(max_length=255, blank=True)

    geo_shape_file = models.ForeignKey(File, on_delete=models.SET_NULL,
                                       null=True, blank=True, default=None)
    tolerance = models.FloatField(default=0.0001)

    stale_geo_areas = models.BooleanField(default=True)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['level']

    def clone_to(self, region, parent=None):
        admin_level = AdminLevel(
            region=region,
            parent=parent,
            title=self.title,
            name_prop=self.name_prop,
            code_prop=self.code_prop,
            parent_name_prop=self.parent_name_prop,
            parent_code_prop=self.parent_code_prop,
            geo_shape_file=self.geo_shape_file,
            tolerance=self.tolerance,
        )
        admin_level.stale_geo_areas = True
        admin_level.save()

        # new_parent_areas = []
        # for area in self.geoarea_set.all():
        #     parent = None
        #     if area.parent:
        #         parent = next((p for p in new_parent_areas
        #                       if p.title == area.parent.title and
        #                       p.code == area.parent.code), None)
        #     new_parent_areas.append(area.clone_to(self, parent))

        for child_level in self.adminlevel_set.all():
            child_level.clone_to(region, admin_level)

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
    polygons = models.GeometryField(null=True, blank=True, default=None)

    long_label = models.TextField(blank=True)
    short_label = models.TextField(blank=True)

    def __str__(self):
        return self.get_label()

    def save(self, *args, **kwargs):
        self.long_label = self.get_label()
        self.short_label = self.get_label(False)
        super(GeoArea, self).save(*args, **kwargs)

    def get_label(self, prepend_region=True):
        if self.parent:
            return '{} / {}'.format(
                self.parent.get_label(prepend_region),
                self.title,
            )
        if prepend_region and self.admin_level.region.title != self.title:
            return '{} / {}'.format(
                self.admin_level.region.title,
                self.title,
            )
        return self.title

    def clone_to(self, admin_level, parent):
        geo_area = GeoArea(
            admin_level=admin_level,
            parent=parent,
            title='{} (cloned)'.format(self.title),
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
