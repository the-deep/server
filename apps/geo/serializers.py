from django.conf import settings
from django.db import transaction
from drf_dynamic_fields import DynamicFieldsMixin

from deep.serializers import (
    ProjectPropertySerializerMixin,
    RemoveNullFieldsMixin,
    URLCachedFileField,
)
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
    is_published = serializers.BooleanField(read_only=True)

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

    def validate(self, data):
        if self.instance and self.instance.is_published:
            raise serializers.ValidationError('Published region can\'t be changed. Please contact Admin')
        return data

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


class RegionGqSerializer(ProjectPropertySerializerMixin, UserResourceSerializer):
    project = serializers.PrimaryKeyRelatedField(queryset=Project.objects.all())
    client_id = serializers.CharField(required=False)

    class Meta:
        model = Region
        fields = ['title', 'code', 'project', 'client_id']

    def validate_project(self, project):
        if not project.can_modify(self.context['request'].user):
            raise serializers.ValidationError('Permission Denied')
        return project

    def validate(self, data):
        if self.instance and self.instance.is_published:
            raise serializers.ValidationError('Published region can\'t be changed. Please contact Admin')
        return data

    def create(self, validated_data):
        project = validated_data.pop('project', None)
        region = super().create(validated_data)
        project.regions.add(region)
        return region


class AdminLevelGqlSerializer(UserResourceSerializer):
    region = serializers.PrimaryKeyRelatedField(queryset=Region.objects.all())

    class Meta:
        model = AdminLevel
        exclude = ('geo_area_titles',)

    def validate_region(self, region):
        if not region.can_modify(self.context['request'].user):
            raise serializers.ValidationError('Invalid Region')
        if region.is_published:
            raise serializers.ValidationError('The AdminLevel cannot be altered once the region has been published.')
        return region

    def create(self, validated_data):
        admin_level = super().create(validated_data)

        if not settings.TESTING:
            transaction.on_commit(lambda: load_geo_areas.delay(region.id))

        return admin_level

    def update(self, instance, validated_data):
        if instance.region.id != validated_data['region'].id:
            raise serializers.ValidationError("Admin Level is not associated with the region")
        admin_level = super().update(
            instance,
            validated_data,
        )
        admin_level.save()

        region = admin_level.region
        region.modified_by = self.context['request'].user
        region.save()

        if not settings.TESTING:
            transaction.on_commit(lambda: load_geo_areas.delay(region.id))

        return admin_level
