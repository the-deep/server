from django.shortcuts import get_object_or_404
from drf_dynamic_fields import DynamicFieldsMixin
from rest_framework import serializers

from deep.serializers import RemoveNullFieldsMixin
from user.serializers import SimpleUserSerializer
from user_resource.serializers import UserResourceSerializer
from project.serializers import ProjectEntitySerializer
from gallery.serializers import SimpleFileSerializer
from user.models import User
from .models import (
    LeadGroup,
    Lead,
    LeadPreviewImage,
)


def check_if_url_exists(url, user=None, project=None, exception_id=None):
    if not project and user:
        return url and Lead.get_for(user).filter(
            url__icontains=url,
        ).exclude(id=exception_id).exists()
    elif project:
        return url and Lead.objects.filter(
            url__icontains=url,
            project=project,
        ).exclude(id=exception_id).exists()
    return False


# TODO: Remove this once assignee is working in browser
#       extension.
# This field checks if incoming data is list
# and if so returns first element of the list.
# Else it returns the value itself.
class SingleValueThayMayBeListField(serializers.Field):
    def to_representation(self, obj):
        return obj

    def to_internal_value(self, data):
        if isinstance(data, list):
            return data[0]
        return data


class SimpleLeadSerializer(RemoveNullFieldsMixin,
                           serializers.ModelSerializer):
    class Meta:
        model = Lead
        fields = ('id', 'title', 'source', 'created_at', 'created_by')


class LeadSerializer(RemoveNullFieldsMixin,
                     DynamicFieldsMixin, ProjectEntitySerializer):
    """
    Lead Model Serializer
    """
    no_of_entries = serializers.IntegerField(read_only=True)
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
    assignee = SingleValueThayMayBeListField(
        source='get_assignee.id',
        required=False,
    )

    class Meta:
        model = Lead
        fields = ('__all__')

    def validate(self, data):
        project = data.get('project',
                           self.instance and self.instance.project)
        source_type = data.get('source_type',
                               self.instance and self.instance.source_type)

        # For website types, check if url has already been added
        if source_type == Lead.WEBSITE:
            url = data.get('url',
                           self.instance and self.instance.url)
            if check_if_url_exists(url, None, project,
                                   self.instance and self.instance.id):
                raise serializers.ValidationError(
                    'A lead with this URL has already been added to '
                    'this project'
                )

        return data

    # TODO: Probably also validate assignee to valid list of users

    def create(self, validated_data):
        assignee_field = validated_data.pop('get_assignee', None)
        assignee_id = assignee_field and assignee_field.get('id', None)
        assignee = assignee_id and get_object_or_404(User, id=assignee_id)

        lead = super().create(validated_data)
        if assignee:
            lead.assignee.add(assignee)
        return lead

    def update(self, instance, validated_data):
        assignee_field = validated_data.pop('get_assignee', None)
        assignee_id = assignee_field and assignee_field.get('id', None)
        assignee = assignee_id and get_object_or_404(User, id=assignee_id)

        lead = super().update(instance, validated_data)
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
    no_of_leads = serializers.IntegerField(read_only=True)

    class Meta:
        model = LeadGroup
        fields = ('__all__')
