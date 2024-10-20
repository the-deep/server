from rest_framework import serializers
from user_resource.serializers import UserResourceSerializer
from drf_dynamic_fields import DynamicFieldsMixin

from geo.serializers import SimpleRegionSerializer
from deep.serializers import URLCachedFileField, RemoveNullFieldsMixin

from .models import Organization, OrganizationType


class OrganizationTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrganizationType
        fields = ('__all__')


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


class OrganizationSerializer(
    DynamicFieldsMixin, RemoveNullFieldsMixin, UserResourceSerializer,
):
    organization_type_display = OrganizationTypeSerializer(
        source='organization_type', read_only=True,
    )
    regions_display = SimpleRegionSerializer(
        source='regions', read_only=True, many=True,
    )
    logo_url = URLCachedFileField(source='logo.file', allow_null=True, required=False)
    merged_as = MergedAsOrganizationSerializer(source='parent', read_only=True)
    client_id = None

    class Meta:
        model = Organization
        exclude = ('parent',)
        read_only_fields = ('verified', 'logo_url',)

    def create(self, validated_data):
        organization = super().create(validated_data)
        organization.created_by = organization.modified_by = self.context['request'].user
        return organization


def get_merged_as(self, obj):
    if obj and obj.parent_id:
        return OrganizationSerializer(obj.parent, context=self.context).data


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
