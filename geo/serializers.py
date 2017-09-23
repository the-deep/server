import json
from django.conf import settings
from rest_framework import serializers
from .models import Region, AdminLevel  # , GeoShape
from .tasks import load_geo_areas


class RegionSerializer(serializers.ModelSerializer):
    """
    Region Model Serializer
    """
    class Meta:
        model = Region
        fields = ('pk', 'code', 'title', 'data', 'is_global')


class AdminLevelSerializer(serializers.ModelSerializer):
    """
    Admin Level Model Serializer
    """

    class Meta:
        model = AdminLevel
        fields = ('pk', 'title', 'name_prop', 'code_prop', 'parent_name_prop',
                  'parent_code_prop', 'region', 'parent', 'geo_shape',)
        read_only_fields = ('geo_shape',)


class AdminLevelUploadSerializer(serializers.ModelSerializer):
    """
    Admin Level Upload Serializer [Geo file]
    """
    geo_shape = serializers.FileField(max_length=100000)

    def update(self, instance, validated_data):

        if not settings.TESTING:
            load_geo_areas.delay(instance.region.pk)

        self.fields.pop('geo_shape')
        instance.geo_shape = json.loads(
                validated_data.pop('geo_shape').read().decode('utf-8'))
        instance.save()
        return instance

    class Meta:
        model = AdminLevel
        fields = ('pk', 'geo_shape',)
