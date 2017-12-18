# from django.conf import settings
from drf_dynamic_fields import DynamicFieldsMixin
from rest_framework import serializers
from user_resource.serializers import UserResourceSerializer
from geo.models import Region, AdminLevel  # , GeoShape
from project.models import Project
# from .tasks import load_geo_areas


class SimpleRegionSerializer(serializers.ModelSerializer):
    title = serializers.CharField(read_only=True)

    class Meta:
        model = Region
        fields = ('id', 'title')


class SimpleAdminLevelSerializer(serializers.ModelSerializer):
    class Meta:
        model = AdminLevel
        fields = ('id', 'title', 'name_prop', 'code_prop',
                  'parent_name_prop', 'parent_code_prop',)


class RegionSerializer(DynamicFieldsMixin, UserResourceSerializer):
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
        fields = ('__all__')

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
        region = super(RegionSerializer, self).create(validated_data)

        if project:
            project = Project.objects.get(id=project)
            project.regions.add(region)

        return region


class AdminLevelSerializer(DynamicFieldsMixin, serializers.ModelSerializer):
    """
    Admin Level Model Serializer
    """

    class Meta:
        model = AdminLevel
        fields = ('__all__')

    # Validations
    def validate_region(self, region):
        if not region.can_modify(self.context['request'].user):
            raise serializers.ValidationError('Invalid region')
        return region

    def create(self, validated_data):
        admin_level = super(AdminLevelSerializer, self).create(validated_data)
        admin_level.save()

        region = admin_level.region
        region.modified_by = self.context['request'].user
        region.save()

        return admin_level

    def update(self, validated_data):
        admin_level = super(AdminLevelSerializer, self).update(validated_data)
        admin_level.save()

        region = admin_level.region
        region.modified_by = self.context['request'].user
        region.save()

        return admin_level
