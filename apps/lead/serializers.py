from django.shortcuts import get_object_or_404
from django.db import transaction
from drf_dynamic_fields import DynamicFieldsMixin
from rest_framework import serializers

from deep.serializers import RemoveNullFieldsMixin, URLCachedFileField
from organization.serializers import SimpleOrganizationSerializer
from user.serializers import SimpleUserSerializer
from user_resource.serializers import UserResourceSerializer
from project.serializers import ProjectEntitySerializer
from gallery.serializers import SimpleFileSerializer, File
from user.models import User
from .models import (
    LeadGroup,
    Lead,
    LeadPreviewImage,
    LeadEMMTrigger,
    EMMEntity,
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


class EMMEntitySerializer(serializers.Serializer, RemoveNullFieldsMixin, DynamicFieldsMixin):
    name = serializers.CharField()

    class Meta:
        fields = '__all__'


class SimpleLeadSerializer(RemoveNullFieldsMixin,
                           serializers.ModelSerializer):
    class Meta:
        model = Lead
        fields = (
            'id', 'title', 'created_at', 'created_by',
            'source_raw', 'author_raw',
            'source', 'author',
        )
        # Legacy Fields
        read_only_fields = ('author_raw', 'source_raw',)


class LegacySimpleLeadSerializer(SimpleLeadSerializer):
    source = serializers.CharField(source='source_raw')
    author = serializers.CharField(source='author_raw')

    class Meta:
        model = Lead
        fields = (
            'id', 'title', 'created_at', 'created_by',
            'source', 'author',
        )


class LeadEMMTriggerSerializer(serializers.ModelSerializer, RemoveNullFieldsMixin, DynamicFieldsMixin):
    emm_risk_factor = serializers.CharField(required=False)
    count = serializers.IntegerField(required=False)

    class Meta:
        model = LeadEMMTrigger
        fields = ('emm_risk_factor', 'emm_keyword', 'count',)


class LeadSerializer(
    RemoveNullFieldsMixin, DynamicFieldsMixin, ProjectEntitySerializer
):
    """
    Lead Model Serializer
    """
    no_of_entries = serializers.IntegerField(read_only=True)
    attachment = SimpleFileSerializer(required=False)
    thumbnail = URLCachedFileField(
        source='leadpreview.thumbnail',
        read_only=True,
    )
    thumbnail_height = serializers.IntegerField(
        source='leadpreview.thumbnail_height',
        read_only=True,
    )
    thumbnail_width = serializers.IntegerField(
        source='leadpreview.thumbnail_width',
        read_only=True,
    )
    word_count = serializers.IntegerField(
        source='leadpreview.word_count',
        read_only=True,
    )
    page_count = serializers.IntegerField(
        source='leadpreview.page_count',
        read_only=True,
    )
    classified_doc_id = serializers.IntegerField(
        source='leadpreview.classified_doc_id',
        read_only=True,
    )

    author_detail = SimpleOrganizationSerializer(source='author', read_only=True)
    source_detail = SimpleOrganizationSerializer(source='source', read_only=True)

    assignee_details = SimpleUserSerializer(
        source='get_assignee',
        # many=True,
        read_only=True,
    )
    assignee = SingleValueThayMayBeListField(
        source='get_assignee.id',
        required=False,
    )
    tabular_book = serializers.SerializerMethodField()
    emm_triggers = LeadEMMTriggerSerializer(many=True, required=False)
    emm_entities = EMMEntitySerializer(many=True, required=False)

    class Meta:
        model = Lead
        fields = ('__all__')
        # Legacy Fields
        read_only_fields = ('author_raw', 'source_raw',)

    def get_tabular_book(self, obj):
        file = obj.attachment
        if file and hasattr(file, 'book'):
            return file.book.id
        return None

    @staticmethod
    def add_update__validate(data, instance, attachment=None):
        project = data.get('project', instance and instance.project)
        source_type = data.get('source_type', instance and instance.source_type)
        text = data.get('text', instance and instance.text)

        # For website types, check if url has already been added
        if source_type == Lead.WEBSITE:
            url = data.get('url', instance and instance.url)
            if check_if_url_exists(url, None, project, instance and instance.pk):
                raise serializers.ValidationError(
                    'A lead with this URL has already been added to '
                    'this project'
                )
        # For attachment types, check if file already used (using file hash)
        elif (
            attachment and attachment.metadata and
            source_type in [Lead.DISK, Lead.DROPBOX, Lead.GOOGLE_DRIVE]
        ):
            if Lead.objects.filter(
                project=project,
                attachment__metadata__md5_hash=attachment.metadata.get('md5_hash'),
            ).exclude(pk=instance and instance.pk).exists():
                raise serializers.ValidationError(
                    f'A lead with this file has already been added to this project'
                )
        elif source_type == Lead.TEXT:
            if Lead.objects.filter(
                project=project,
                text=text,
            ).exclude(pk=instance and instance.pk).exists():
                raise serializers.ValidationError(
                    f'A lead with this text has already been added to this project'
                )

    def validate(self, data):
        attachment_id = self.get_initial().get('attachment', {}).get('id')
        LeadSerializer.add_update__validate(
            data, self.instance,
            File.objects.filter(pk=attachment_id).first()
        )
        return data

    # TODO: Probably also validate assignee to valid list of users

    def create(self, validated_data):
        assignee_field = validated_data.pop('get_assignee', None)
        assignee_id = assignee_field and assignee_field.get('id', None)
        assignee = assignee_id and get_object_or_404(User, id=assignee_id)

        emm_triggers = validated_data.pop('emm_triggers', [])
        emm_entities = validated_data.pop('emm_entities', [])

        lead = super().create(validated_data)

        for entity in emm_entities:
            entity = EMMEntity.objects.filter(name=entity['name']).first()
            if entity is None:
                continue
            lead.emm_entities.add(entity)
        lead.save()

        with transaction.atomic():
            for trigger in emm_triggers:
                LeadEMMTrigger.objects.create(**trigger, lead=lead)

        if assignee:
            lead.assignee.add(assignee)
        return lead

    def update(self, instance, validated_data):
        assignee_field = validated_data.pop('get_assignee', None)
        assignee_id = assignee_field and assignee_field.get('id', None)
        assignee = assignee_id and get_object_or_404(User, id=assignee_id)

        # We do not update triggers and entities
        validated_data.pop('emm_entities', [])
        validated_data.pop('emm_triggers', [])

        lead = super().update(instance, validated_data)

        if assignee_field:
            lead.assignee.clear()
            if assignee:
                lead.assignee.add(assignee)
        return lead


# Legacy
class LegacyLeadSerializer(LeadSerializer):
    author_detail = None
    source_detail = None

    source = serializers.CharField(source='source_raw')
    author = serializers.CharField(source='author_raw')

    class Meta:
        model = Lead
        exclude = ('source_raw', 'author_raw',)


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


class SimpleLeadGroupSerializer(UserResourceSerializer):
    class Meta:
        model = LeadGroup
        fields = ('id', 'title',)
