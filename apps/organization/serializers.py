from rest_framework import serializers
from user_resource.serializers import UserResourceSerializer
from drf_dynamic_fields import DynamicFieldsMixin

from deep.serializers import URLCachedFileField

from .models import Organization


class MergedAsOrganizationSerializer(serializers.ModelSerializer):
    logo = URLCachedFileField(source='logo.file', read_only=True)

    class Meta:
        model = Organization
        fields = ('id', 'title', 'logo')


class SimpleOrganizationSerializer(serializers.ModelSerializer):
    logo = URLCachedFileField(source='logo.file', read_only=True)
    merged_as = MergedAsOrganizationSerializer(source='parent', read_only=True)

    class Meta:
        model = Organization
        fields = ('id', 'title', 'short_name', 'merged_as', 'logo')


class ArySourceOrganizationSerializer(DynamicFieldsMixin, UserResourceSerializer):
    logo = URLCachedFileField(source='logo.file', allow_null=True)
    key = serializers.IntegerField(source='pk')
    merged_as = MergedAsOrganizationSerializer(source='parent', read_only=True)

    class Meta:
        model = Organization
        fields = ('key', 'title', 'long_name',
                  'short_name', 'logo', 'organization_type', 'merged_as')


class OrganizationGqSerializer(UserResourceSerializer):
    class Meta:
        model = Organization
        fields = ('title', 'long_name', 'url', 'short_name', 'logo', 'organization_type')
