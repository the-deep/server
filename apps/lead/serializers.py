import copy

from django.shortcuts import get_object_or_404
from django.db import transaction
from drf_dynamic_fields import DynamicFieldsMixin
from rest_framework import serializers
from django.utils import timezone

from deep.permissions import ProjectPermissions as PP
from deep.serializers import (
    RemoveNullFieldsMixin,
    TempClientIdMixin,
    IntegerIDField,
    URLCachedFileField,
    IdListField,
    StringListField,
    WriteOnlyOnCreateSerializerMixin,
    ProjectPropertySerializerMixin,
)
from organization.serializers import SimpleOrganizationSerializer
from user.serializers import SimpleUserSerializer
from user_resource.serializers import UserResourceSerializer
from project.serializers import SimpleProjectSerializer
from gallery.serializers import SimpleFileSerializer, File
from user.models import User
from project.models import ProjectMembership
from unified_connector.models import ConnectorSourceLead

from .tasks import LeadExtraction
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

    if source_type == Lead.SourceType.WEBSITE:
        existing_lead = check_if_url_exists(url, None, project, lead and lead.pk, return_lead=return_lead)
        error_message = f'A source with this URL has already been added to Project: {project}'
    elif (
        attachment and attachment.metadata and
        source_type in [Lead.SourceType.DISK, Lead.SourceType.DROPBOX, Lead.SourceType.GOOGLE_DRIVE]
    ):
        # For attachment types, check if file already used (using file hash)
        existing_lead = Lead.objects.filter(
            project=project,
            attachment__metadata__md5_hash=attachment.metadata.get('md5_hash'),
        ).exclude(pk=lead and lead.pk).first()
        error_message = f'A source with this file has already been added to Project: {project}'
    elif source_type == Lead.SourceType.TEXT:
        existing_lead = Lead.objects.filter(
            project=project,
            text=text,
        ).exclude(pk=lead and lead.pk).first()
        error_message = f'A source with this text has already been added to Project: {project}'

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
    RemoveNullFieldsMixin, DynamicFieldsMixin, WriteOnlyOnCreateSerializerMixin, UserResourceSerializer,
):
    """
    Lead Model Serializer
    """
    # annotated in lead.get_for
    entries_count = serializers.IntegerField(read_only=True)
    controlled_entries_count = serializers.IntegerField(read_only=True)
    filtered_entries_count = serializers.IntegerField(read_only=True)
    controlled_filtered_entries_count = serializers.IntegerField(read_only=True)

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
        read_only_fields = ('author_raw', 'source_raw')
        write_only_on_create_fields = ['emm_triggers', 'emm_entities']

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

    def validate_is_assessment_lead(self, value):
        # Allow setting True
        # For False make sure there are no assessment attached.
        if value is False and hasattr(self.instance, 'assessment'):
            raise serializers.ValidationError('Lead already has an assessment.')
        return value

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
        emm_entities_names = [
            entity['name']
            for entity in validated_data.pop('emm_entities', [])
            if isinstance(entity, dict) and 'name' in entity
        ]

        lead = super().create(validated_data)

        for entity in EMMEntity.objects.filter(name__in=emm_entities_names):
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
        validated_data.pop('emm_entities', None)
        validated_data.pop('emm_triggers', None)

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

    file = URLCachedFileField(read_only=True)

    class Meta:
        model = LeadPreviewImage
        fields = ('id', 'file',)


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
    organization_types = KeyValueSerializer(many=True)


class LeadOptionsBodySerializer(serializers.Serializer):
    projects = IdListField()
    lead_groups = IdListField()
    organizations = IdListField()
    members = IdListField()
    emm_entities = IdListField()
    emm_keywords = StringListField()
    emm_risk_factors = StringListField()
    organization_types = IdListField()


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
    organization_types = KeyValueSerializer(many=True)


# ------------------- Graphql Serializers ----------------------------------------
class LeadGqSerializer(ProjectPropertySerializerMixin, TempClientIdMixin, UserResourceSerializer):
    """
    Lead Model Serializer for Graphql (NOTE: Don't use this on DRF Views)
    """
    id = IntegerIDField(required=False)
    # TODO: Make assigne Foreign key from M2M Field
    assignee = SingleValueThayMayBeListField(required=False)
    # NOTE: Right now this is send to client through connector and then return back to server (Only needed on create)
    emm_triggers = LeadEMMTriggerSerializer(many=True, required=False)
    emm_entities = EMMEntitySerializer(many=True, required=False)

    class Meta:
        model = Lead
        fields = (
            'id',
            'title',
            'attachment',
            'status',
            'assignee',
            'confidentiality',
            'source_type',
            'priority',
            'published_on',
            'text',
            'is_assessment_lead',
            'lead_group',
            'url',
            'website',
            'source',
            'authors',
            'emm_triggers',
            'emm_entities',
            'connector_lead',
            'client_id',  # From TempClientIdMixin
        )

    def validate_attachment(self, attachment):
        # If attachment is None or isn't changed.
        if attachment is None or (self.instance and self.instance.attachment_id == attachment.id):
            return attachment
        # For new attachment make sure user have permission to attach.
        if attachment.created_by != self.context['request'].user:
            raise serializers.ValidationError("Attachment not found or you don't have the permission!")
        return attachment

    def validate_assignee(self, assignee_id):
        assignee = self.project.get_all_members().filter(id=assignee_id).first()
        if assignee is None:
            raise serializers.ValidationError('Only project members can be assigneed')
        return assignee

    def validate_lead_group(self, lead_group):
        if lead_group and lead_group.project_id != self.project.id:
            raise serializers.ValidationError('LeadGroup should have same project as lead project')
        return lead_group

    def validate_is_assessment_lead(self, value):
        # Allow setting True
        # For False make sure there are no assessment attached.
        if value is False and hasattr(self.instance, 'assessment'):
            raise serializers.ValidationError('Lead already has an assessment.')
        return value

    def validate(self, data):
        """
        This validator makes sure there is no duplicate leads in a project
        """
        # Using active project here.
        data['project'] = self.project
        attachment = data.get('attachment', self.instance and self.instance.attachment)
        source_type = data.get('source_type', self.instance and self.instance.source_type)
        text = data.get('text', self.instance and self.instance.text)
        url = data.get('url', self.instance and self.instance.url)
        raise_or_return_existing_lead(
            data['project'], self.instance, source_type, url, text, attachment,
            return_lead=False,  # Raise exception
        )
        return data

    def create(self, validated_data):
        assignee = validated_data.pop('assignee', None)
        # Pop out emm values from validated_data
        emm_triggers = validated_data.pop('emm_triggers', [])
        emm_entities = validated_data.pop('emm_entities', [])
        # Create new lead
        lead = super().create(validated_data)
        # Save emm entities
        for entity in emm_entities:
            entity = EMMEntity.objects.filter(name=entity['name']).first()
            if entity is None:
                continue
            lead.emm_entities.add(entity)
        # Save emm triggers
        for trigger in emm_triggers:
            LeadEMMTrigger.objects.create(**trigger, lead=lead)
        # Save Assignee
        if assignee:
            lead.assignee.add(assignee)
        # If connector lead is provided, set already_added for all connector leads
        if validated_data['connector_lead']:
            ConnectorSourceLead.update_aleady_added_using_lead(lead, added=True)
            ConnectorSourceLead.objects.filter(
                connector_lead=lead.connector_lead,
                source__unified_connector__project=lead.project,
            ).update(already_added=True)
        return lead

    def update(self, instance, validated_data):
        has_assignee = 'assignee' in validated_data  # For parital updates
        assignee = validated_data.pop('assignee', None)
        # Pop out emm values from validated_data (Only allowed in creation)
        validated_data.pop('emm_triggers', [])
        validated_data.pop('emm_entities', [])
        # Save lead
        lead = super().update(instance, validated_data)
        if has_assignee:
            lead.assignee.clear()
            if assignee:
                lead.assignee.add(assignee)
        return lead


class LeadCopyGqSerializer(ProjectPropertySerializerMixin, serializers.Serializer):
    MAX_PROJECTS_ALLOWED = 10
    MAX_LEADS_ALLOWED = 100

    projects = serializers.ListField(
        child=IntegerIDField(),
        required=True
    )
    leads = serializers.ListField(
        child=IntegerIDField(),
        required=True,
    )

    def validate_projects(self, projects_id):
        projects_id = list(
            ProjectMembership.objects.filter(
                member=self.context['request'].user,
                role__type__in=PP.REVERSE_PERMISSION_MAP[PP.Permission.CREATE_LEAD],
                project__in=projects_id,
            ).values_list('project', flat=True).distinct()
        )
        count = len(projects_id)
        if count > self.MAX_PROJECTS_ALLOWED:
            raise serializers.ValidationError(f'Only {self.MAX_PROJECTS_ALLOWED} are allowed. Provided: {count}')
        return projects_id

    def validate_leads(self, leads_id):
        allowed_permission = self.context['request'].project_permissions
        lead_qs = Lead.objects.filter(
            id__in=leads_id,
            project=self.project,
        )
        if PP.Permission.VIEW_ALL_LEAD in allowed_permission:
            pass
        elif PP.Permission.VIEW_ONLY_UNPROTECTED_LEAD in allowed_permission:
            lead_qs = lead_qs.filter(confidentiality=Lead.Confidentiality.UNPROTECTED).all()
        else:
            raise serializers.ValidationError("You don't have lead read access")
        count = lead_qs.count()
        if count > self.MAX_LEADS_ALLOWED:
            raise serializers.ValidationError(f'Only {self.MAX_LEADS_ALLOWED} are allowed. Provided: {count}')
        return lead_qs

    def clone_lead(self, original_lead, project_id, user):
        new_lead = copy.deepcopy(original_lead)

        def _get_clone_ready(obj, lead):
            obj.pk = None
            obj.lead = lead
            return obj

        new_lead.pk = None
        existing_lead = raise_or_return_existing_lead(
            project_id,
            new_lead,
            new_lead.source_type,
            new_lead.url,
            new_lead.text,
            new_lead.attachment,
            return_lead=True
        )
        if existing_lead:
            return

        preview = original_lead.leadpreview if hasattr(original_lead, 'leadpreview') else None
        preview_images = original_lead.images.all()
        emm_triggers = original_lead.emm_triggers.all()
        emm_entities = original_lead.emm_entities.all()
        authors = original_lead.authors.all()

        # NOTE: Don't copy lead_group for now
        new_lead.lead_group = None
        new_lead.project_id = project_id
        new_lead.client_id = None

        # update the fields for copied lead
        new_lead.created_at = timezone.now()
        new_lead.created_by = new_lead.modified_by = self.context['request'].user
        new_lead.status = Lead.Status.NOT_TAGGED
        new_lead.save()

        # Clone Lead Preview (One-to-one fields)
        if preview:
            preview.pk = None
            preview.lead = new_lead
            preview.save()

        # Clone Many to many Fields
        new_lead.assignee.add(user)  # Assign requesting user
        new_lead.emm_entities.set(emm_entities)
        new_lead.authors.set(authors)

        # Clone Many to one Fields
        LeadPreviewImage.objects.bulk_create([
            _get_clone_ready(image, new_lead) for image in preview_images
        ])
        LeadEMMTrigger.objects.bulk_create([
            _get_clone_ready(emm_trigger, new_lead) for emm_trigger in emm_triggers
        ])

        return new_lead

    def create(self, validated_data):
        projects_id = validated_data.get('projects', [])
        leads = validated_data.get('leads', [])
        user = self.context['request'].user
        new_leads = []
        for project_id in projects_id:
            for lead in leads:
                new_lead = self.clone_lead(lead, project_id, user)
                new_lead and new_leads.append(new_lead)
        return new_leads


class ExtractCallbackSerializer(serializers.Serializer):
    """
    Serialize deepl extractor
    """
    client_id = serializers.CharField()
    images_path = serializers.ListField(
        child=serializers.CharField(allow_blank=True), default=[]
    )
    text_path = serializers.CharField()
    url = serializers.CharField()
    total_words_count = serializers.IntegerField()
    total_pages = serializers.IntegerField()
    extraction_status = serializers.IntegerField()  # 0 = Failed, 1 = Success

    def validate_client_id(self, data):
        client_id = data['client_id']
        try:
            data['lead'] = LeadExtraction.get_lead_from_client_id(client_id)
        except Exception as e:
            raise serializers.ValidationError(str(e))
        return data

    def create(self, data):
        return LeadExtraction.save_lead_data(
            data['lead'],  # Added from validate
            data['extraction_status'] == 1,
            data['text_path'],
            data['images_path'],
            data['total_words_count'],
            data['total_pages'],
        )
