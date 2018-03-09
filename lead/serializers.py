from drf_dynamic_fields import DynamicFieldsMixin
from rest_framework import serializers
from user_resource.serializers import UserResourceSerializer
from gallery.serializers import SimpleFileSerializer
from .models import (
    Lead,
    LeadPreviewImage,
)


class SimpleLeadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lead
        fields = ('id', 'title', 'source', 'created_at', 'created_by')


class LeadSerializer(DynamicFieldsMixin, UserResourceSerializer):
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
    assessment = serializers.SerializerMethodField()

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

    def get_assessment(self, lead):
        assessment = lead.assessment_set.first()
        if assessment:
            return assessment.pk


class LeadPreviewImageSerializer(
        DynamicFieldsMixin, serializers.ModelSerializer):
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


class LeadPreviewSerializer(DynamicFieldsMixin, serializers.ModelSerializer):
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
