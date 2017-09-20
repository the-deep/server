from rest_framework import serializers
from .models import Region, AdminLevel  # , GeoShape


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
        fields = ('pk', 'title', 'name_prop', 'pcode_prop', 'parent_name_prop',
                  'parent_pcode_prop', 'region', 'parent', 'geo_shape',)


class AdminLevelUploadSerializer(serializers.ModelSerializer):
    """
    Admin Level Upload Serializer [Geo file]
    """
    geo_shape = serializers.FileField(max_length=100000)

    def update(self, instance, validated_data):
        # Add geo extraction job
        # validated_date.pop('geo_shape') is the file
        return instance

    class Meta:
        model = AdminLevel
        fields = ('pk', 'geo_shape',)
