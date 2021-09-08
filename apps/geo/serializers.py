from django.conf import settings
from django.db import transaction
from drf_dynamic_fields import DynamicFieldsMixin

from deep.serializers import RemoveNullFieldsMixin, URLCachedFileField
from rest_framework import serializers
from user_resource.serializers import UserResourceSerializer
from geo.models import (
    Region,
    AdminLevel,
    GeoArea
)
from geo.tasks import load_geo_areas
from project.models import Project
from gallery.serializers import SimpleFileSerializer


class SimpleRegionSerializer(RemoveNullFieldsMixin,
                             serializers.ModelSerializer):
    title = serializers.CharField(read_only=True)

    class Meta:
        model = Region
        fields = ('id', 'title')


class SimpleAdminLevelSerializer(RemoveNullFieldsMixin,
                                 serializers.ModelSerializer):
    class Meta:
        model = AdminLevel
        fields = ('id', 'title', 'level', 'name_prop', 'code_prop',
                  'parent_name_prop', 'parent_code_prop',)


class RegionSerializer(RemoveNullFieldsMixin,
                       DynamicFieldsMixin, UserResourceSerializer):
    """
    Region Model Serializer
    """
    admin_levels = SimpleAdminLevelSerializer(
        many=True,
        source='adminlevel_set',
        read_only=True,
    )

    project = serializers.IntegerField(
        write_only=True,
        required=False,
    )

    class Meta:
        model = Region
        exclude = ('geo_options',)

    def validate_project(self, project):
        try:
            project = Project.objects.get(id=project)
        except Project.DoesNotExist:
            raise serializers.ValidationError(
                'Project matching query does not exist'
            )

        if not project.can_modify(self.context['request'].user):
            raise serializers.ValidationError('Invalid project')
        return project.id

    def create(self, validated_data):
        project = validated_data.pop('project', None)
        region = super().create(validated_data)

        if project:
            project = Project.objects.get(id=project)
            project.regions.add(region)

        return region


class AdminLevelSerializer(RemoveNullFieldsMixin,
                           DynamicFieldsMixin, serializers.ModelSerializer):
    """
    Admin Level Model Serializer
    """
    geo_shape_file_details = SimpleFileSerializer(source='geo_shape_file', read_only=True)

    geojson_file = URLCachedFileField(required=False, read_only=True)
    bounds_file = URLCachedFileField(required=False, read_only=True)

    class Meta:
        model = AdminLevel
        exclude = ('geo_area_titles',)

    # Validations
    def validate_region(self, region):
        if not region.can_modify(self.context['request'].user):
            raise serializers.ValidationError('Invalid region')
        return region

    def create(self, validated_data):
        admin_level = super().create(validated_data)
        admin_level.stale_geo_areas = True
        admin_level.save()

        region = admin_level.region
        region.modified_by = self.context['request'].user
        region.save()

        if not settings.TESTING:
            transaction.on_commit(lambda: load_geo_areas.delay(region.id))

        return admin_level

    def update(self, instance, validated_data):
        admin_level = super().update(
            instance,
            validated_data,
        )
        admin_level.stale_geo_areas = True
        admin_level.save()

        region = admin_level.region
        region.modified_by = self.context['request'].user
        region.save()

        if not settings.TESTING:
            transaction.on_commit(lambda: load_geo_areas.delay(region.id))

        return admin_level


class GeoAreaSerializer(serializers.ModelSerializer):
    label = serializers.CharField()
    key = serializers.CharField()
    region = serializers.CharField()
    region_title = serializers.CharField()
    admin_level_level = serializers.CharField()
    admin_level_title = serializers.CharField()

    class Meta:
        model = GeoArea
        fields = (
            'key', 'label', 'region', 'title',
            'region_title', 'admin_level_level', 'admin_level_title',
            'parent'
        )
