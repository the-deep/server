from django.shortcuts import get_object_or_404
from django.db import transaction
from drf_dynamic_fields import DynamicFieldsMixin
from rest_framework import serializers

from deep.serializers import (
    RemoveNullFieldsMixin,
    URLCachedFileField,
    IdListField,
    StringListField,
)
from organization.serializers import SimpleOrganizationSerializer
from user.serializers import SimpleUserSerializer
from user_resource.serializers import UserResourceSerializer
from project.serializers import SimpleProjectSerializer
from gallery.serializers import SimpleFileSerializer, File
from user.models import User
from .models import (
    LeadGroup,
    Lead,
    LeadPreviewImage,
    LeadEMMTrigger,
    EMMEntity,
)


def check_if_url_exists(url, user=None, project=None, exception_id=None, return_lead=False):
    existing_lead = None
    if not project and user:
        existing_lead = url and Lead.get_for(user).filter(
            url__icontains=url,
        ).exclude(id=exception_id).first()
    elif project:
        existing_lead = url and Lead.objects.filter(
            url__icontains=url,
            project=project,
        ).exclude(id=exception_id).first()
    if existing_lead:
        if return_lead:
            return existing_lead
        return True
    return False


def raise_or_return_existing_lead(project, lead, source_type, url, text, attachment, return_lead=False):
    # For website types, check if url has already been added
    existing_lead = None
    error_message = None

    if source_type == Lead.WEBSITE:
        existing_lead = check_if_url_exists(url, None, project, lead and lead.pk, return_lead=return_lead)
        error_message = f'A lead with this URL has already been added to Project: {project}'
    elif (
        attachment and attachment.metadata and
        source_type in [Lead.DISK, Lead.DROPBOX, Lead.GOOGLE_DRIVE]
    ):
        # For attachment types, check if file already used (using file hash)
        existing_lead = Lead.objects.filter(
            project=project,
            attachment__metadata__md5_hash=attachment.metadata.get('md5_hash'),
        ).exclude(pk=lead and lead.pk).first()
        error_message = f'A lead with this file has already been added to Project: {project}'
    elif source_type == Lead.TEXT:
        existing_lead = Lead.objects.filter(
            project=project,
            text=text,
        ).exclude(pk=lead and lead.pk).first()
        error_message = f'A lead with this text has already been added to Project: {project}'

    if existing_lead:
        if return_lead:
            return existing_lead
        raise serializers.ValidationError(error_message)


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


class LeadEMMTriggerSerializer(serializers.ModelSerializer, RemoveNullFieldsMixin, DynamicFieldsMixin):
    emm_risk_factor = serializers.CharField(required=False)
    count = serializers.IntegerField(required=False)

    class Meta:
        model = LeadEMMTrigger
        fields = ('emm_risk_factor', 'emm_keyword', 'count',)


class LeadSerializer(
    RemoveNullFieldsMixin, DynamicFieldsMixin, UserResourceSerializer,
):
    """
    Lead Model Serializer
    """
    no_of_entries = serializers.IntegerField(read_only=True)
    assessment_id = serializers.IntegerField(read_only=True)

    priority_display = serializers.CharField(source='get_priority_display', read_only=True)

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

    # TODO: Remove (Legacy)
    author_detail = SimpleOrganizationSerializer(source='author', read_only=True)

    authors_detail = SimpleOrganizationSerializer(source='authors', many=True, read_only=True)
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
    # extra fields added from entryleadserializer
    confidentiality_display = serializers.CharField(source='get_confidentiality_display', read_only=True)

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
        url = data.get('url', instance and instance.url)

        return raise_or_return_existing_lead(
            project,
            instance,
            source_type,
            url,
            text,
            attachment,
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


class KeyValueSerializer(serializers.Serializer):
    key = serializers.CharField()
    value = serializers.CharField()


class NumericKeyValueSerializer(serializers.Serializer):
    key = serializers.IntegerField()
    value = serializers.CharField()


class EmmTagSerializer(serializers.Serializer):
    key = serializers.CharField()
    label = serializers.CharField()
    total_count = serializers.IntegerField()


class EmmEntitySerializer(serializers.Serializer):
    key = serializers.IntegerField()
    label = serializers.CharField()
    total_count = serializers.IntegerField()


class LegacyLeadOptionsSerializer(serializers.Serializer):
    project = KeyValueSerializer(many=True)
    lead_group = KeyValueSerializer(many=True)
    assignee = KeyValueSerializer(many=True)
    confidentiality = KeyValueSerializer(many=True)
    status = KeyValueSerializer(many=True)
    priority = NumericKeyValueSerializer(many=True)
    emm_entities = EmmEntitySerializer(many=True)
    emm_keywords = EmmTagSerializer(many=True)
    emm_risk_factors = EmmTagSerializer(many=True)
    has_emm_leads = serializers.BooleanField()


class LeadOptionsBodySerializer(serializers.Serializer):
    projects = IdListField()
    lead_groups = IdListField()
    organizations = IdListField()
    members = IdListField()
    emm_entities = IdListField()
    emm_keywords = StringListField()
    emm_risk_factors = StringListField()


class LeadOptionsSerializer(serializers.Serializer):
    projects = SimpleProjectSerializer(many=True)
    confidentiality = KeyValueSerializer(many=True)
    status = KeyValueSerializer(many=True)
    priority = NumericKeyValueSerializer(many=True)
    lead_groups = SimpleLeadGroupSerializer(many=True)
    members = SimpleUserSerializer(many=True)
    organizations = SimpleOrganizationSerializer(many=True)
    emm_entities = EmmEntitySerializer(many=True)
    emm_keywords = EmmTagSerializer(many=True)
    emm_risk_factors = EmmTagSerializer(many=True)
    has_emm_leads = serializers.BooleanField()
