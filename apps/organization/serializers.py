from rest_framework import serializers
from user_resource.serializers import UserResourceSerializer
from drf_dynamic_fields import DynamicFieldsMixin

from geo.serializers import SimpleRegionSerializer
from .models import Organization, OrganizationType


class OrganizationTypeSerializer(serializers.ModelSerializer):

    class Meta:
        model = OrganizationType
        fields = ('__all__')


class OrganizationSerializer(DynamicFieldsMixin, UserResourceSerializer):
    organization_type_display = OrganizationTypeSerializer(
        source='organization_type', read_only=True,
    )
    regions_display = SimpleRegionSerializer(
        source='regions', read_only=True, many=True,
    )
    client_id = None

    class Meta:
        model = Organization
        fields = ('__all__')
        read_only_fields = ('verified',)

    def create(self, validated_data):
        organization = super().create(validated_data)
        organization.created_by = organization.modified_by = self.context['request'].user
        return organization
