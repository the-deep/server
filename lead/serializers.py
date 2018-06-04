from django.shortcuts import get_object_or_404
from drf_dynamic_fields import DynamicFieldsMixin
from rest_framework import serializers

from deep.serializers import RemoveNullFieldsMixin
from user.serializers import SimpleUserSerializer
from user_resource.serializers import UserResourceSerializer
from gallery.serializers import SimpleFileSerializer
from user.models import User
from .models import (
    LeadGroup,
    Lead,
    LeadPreviewImage,
)


class SimpleLeadSerializer(RemoveNullFieldsMixin,
                           serializers.ModelSerializer):
    class Meta:
        model = Lead
        fields = ('id', 'title', 'source', 'created_at', 'created_by')


class LeadSerializer(RemoveNullFieldsMixin,
                     DynamicFieldsMixin, UserResourceSerializer):
    """
    Lead Model Serializer
    """
    no_of_entries = serializers.IntegerField(
        read_only=True,
    )
    attachment = SimpleFileSerializer(required=False)
    classified_doc_id = serializers.IntegerField(
        source='leadpreview.classified_doc_id',
        read_only=True,
    )

    assignee_details = SimpleUserSerializer(
        source='get_assignee',
        # many=True,
        read_only=True,
    )
    assignee = serializers.IntegerField(
        source='get_assignee.id',
        required=False,
    )

    class Meta:
        model = Lead
        fields = ('__all__')

    # validations
    def validate_project(self, project):
        # Make sure we have access to the given project
        if not project.can_get(self.context['request'].user):
            raise serializers.ValidationError(
                'Invalid project: {}'.format(project.id))
        return project

    # TODO: Probably also validate assignee to valid list of users

    def create(self, validated_data):
        assignee_field = validated_data.pop('get_assignee', None)
        assignee_id = assignee_field and assignee_field.get('id', None)
        assignee = assignee_id and get_object_or_404(User, id=assignee_id)

        lead = super(LeadSerializer, self).create(validated_data)
        lead.save()

        if assignee:
            lead.assignee.add(assignee)
        return lead

    def update(self, instance, validated_data):
        assignee_field = validated_data.pop('get_assignee', None)
        assignee_id = assignee_field and assignee_field.get('id', None)
        assignee = assignee_id and get_object_or_404(User, id=assignee_id)

        lead = super(LeadSerializer, self).update(instance, validated_data)
        lead.save()

        if assignee_field:
            lead.assignee.clear()
            if assignee:
                lead.assignee.add(assignee)
        return lead


class LeadPreviewImageSerializer(RemoveNullFieldsMixin,
                                 DynamicFieldsMixin,
                                 serializers.ModelSerializer):
    """
    Serializer for lead preview image
    """

    file = serializers.FileField(required=False)

    class Meta:
        model = LeadPreviewImage
        fields = ('file',)

    def to_representation(self, instance):
        """Convert to string. so leadPreview have array of urls"""
        ret = super().to_representation(instance)
        return ret.get('file')


class LeadPreviewSerializer(RemoveNullFieldsMixin,
                            DynamicFieldsMixin, serializers.ModelSerializer):
    """
    Serializer for lead preview
    """

    text = serializers.CharField(source='leadpreview.text_extract',
                                 read_only=True)
    images = LeadPreviewImageSerializer(many=True, read_only=True)
    classified_doc_id = serializers.IntegerField(
        source='leadpreview.classified_doc_id',
        read_only=True,
    )
    preview_id = serializers.IntegerField(
        source='leadpreview.pk',
        read_only=True,
    )

    class Meta:
        model = Lead
        fields = ('id', 'preview_id', 'text', 'images', 'classified_doc_id')


class LeadGroupSerializer(RemoveNullFieldsMixin,
                          DynamicFieldsMixin, UserResourceSerializer):
    leads = LeadSerializer(source='lead_set',
                           many=True,
                           read_only=True)

    class Meta:
        model = LeadGroup
        fields = ('__all__')
