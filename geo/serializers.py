import json
# from django.conf import settings
from drf_dynamic_fields import DynamicFieldsMixin
from rest_framework import serializers
from user_resource.serializers import UserResourceSerializer
from .models import Region, AdminLevel  # , GeoShape
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

    class Meta:
        model = Region
        fields = ('__all__')


class AdminLevelSerializer(DynamicFieldsMixin, serializers.ModelSerializer):
    """
    Admin Level Model Serializer
    """

    class Meta:
        model = AdminLevel
        fields = ('__all__')
        read_only_fields = ('geo_shape',)

    # Validations
    def validate_region(self, region):
        if not region.can_modify(self.context['request'].user):
            raise serializers.ValidationError('Invalid region')
        return region


class AdminLevelUploadSerializer(DynamicFieldsMixin,
                                 serializers.ModelSerializer):
    """
    Admin Level Upload Serializer [Geo file]
    """
    geo_shape = serializers.FileField(max_length=100000)

    def update(self, instance, validated_data):

        # if not settings.TESTING:
        #     load_geo_areas.delay(instance.region.pk)

        self.fields.pop('geo_shape')
        instance.geo_shape = json.loads(
            validated_data.pop('geo_shape').read().decode('utf-8'))
        instance.save()
        return instance

    class Meta:
        model = AdminLevel
        fields = ('id', 'geo_shape',)
