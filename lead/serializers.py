from drf_dynamic_fields import DynamicFieldsMixin
from rest_framework import serializers
from user_resource.serializers import UserResourceSerializer
from .models import Lead


class LeadSerializer(DynamicFieldsMixin, UserResourceSerializer):
    """
    Lead Model Serializer
    """
    no_of_entries = serializers.IntegerField(
        source='entry_set.count',
        read_only=True)

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


class LeadPreviewSerializer(DynamicFieldsMixin, serializers.ModelSerializer):
    """
    Serializer for lead preview
    """

    text = serializers.CharField(source='leadpreview.text_extract',
                                 read_only=True)
    images = serializers.SerializerMethodField()

    class Meta:
        model = Lead
        fields = ('id', 'text', 'images')

    def get_images(self, lead):
        return [
            image.file.url
            for image in lead.leadpreviewimage_set.all()
        ]
