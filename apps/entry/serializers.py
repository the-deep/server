import logging

from drf_dynamic_fields import DynamicFieldsMixin
from rest_framework import serializers

from deep.serializers import (
    RemoveNullFieldsMixin,
    ListToDictField,
    UniqueFieldsMixin,
)
from organization.serializers import SimpleOrganizationSerializer
from user_resource.serializers import UserResourceSerializer
from gallery.models import File
from gallery.serializers import FileSerializer, SimpleFileSerializer
from project.models import Project
from lead.serializers import LeadSerializer
from lead.models import Lead, LeadPreviewImage
from analysis_framework.serializers import AnalysisFrameworkSerializer
from geo.models import GeoArea, Region
from geo.serializers import SimpleRegionSerializer
from tabular.serializers import FieldProcessedOnlySerializer
from user.serializers import EntryCommentUserSerializer, ComprehensiveUserSerializer, SimpleUserSerializer
from quality_assurance.models import CommentType, EntryReviewComment
from project.models import ProjectMembership

from .widgets.store import widget_store
from .models import (
    Attribute,
    Entry,
    EntryComment,
    EntryCommentText,
    ExportData,
    FilterData,
    # Entry Grouping
    ProjectEntryLabel,
    LeadEntryGroup,
    EntryGroupLabel,
)
from .utils import base64_to_deep_image

logger = logging.getLogger(__name__)


class AttributeSerializer(RemoveNullFieldsMixin,
                          DynamicFieldsMixin, serializers.ModelSerializer):
    class Meta:
        model = Attribute
        fields = '__all__'

    # Validations
    def validate_entry(self, entry):
        if not entry.can_modify(self.context['request'].user):
            raise serializers.ValidationError('Invalid Entry')
        return entry


class FilterDataSerializer(RemoveNullFieldsMixin,
                           DynamicFieldsMixin, serializers.ModelSerializer):
    class Meta:
        model = FilterData
        fields = '__all__'

    # Validations
    def validate_entry(self, entry):
        if not entry.can_modify(self.context['request'].user):
            raise serializers.ValidationError('Invalid Entry')
        return entry


class ExportDataSerializer(RemoveNullFieldsMixin,
                           DynamicFieldsMixin, serializers.ModelSerializer):
    class Meta:
        model = ExportData
        fields = '__all__'

    # Validations
    def validate_entry(self, entry):
        if not entry.can_modify(self.context['request'].user):
            raise serializers.ValidationError('Invalid Entry')
        return entry


class SimpleAttributeSerializer(RemoveNullFieldsMixin,
                                serializers.ModelSerializer):
    class Meta:
        model = Attribute
        fields = ('id', 'data', 'widget',)


class SimpleFilterDataSerializer(RemoveNullFieldsMixin,
                                 serializers.ModelSerializer):
    class Meta:
        model = FilterData
        fields = ('id', 'filter', 'values', 'number',)


class SimpleExportDataSerializer(RemoveNullFieldsMixin,
                                 serializers.ModelSerializer):
    class Meta:
        model = ExportData
        fields = ('id', 'exportable', 'data',)


class ProjectEntryLabelSerializer(DynamicFieldsMixin, UserResourceSerializer):

    class Meta:
        model = ProjectEntryLabel
        fields = '__all__'
        read_only_fields = ('project',)

    def validate(self, data):
        data['project_id'] = int(self.context['view'].kwargs['project_id'])
        return data


class ProjectEntryLabelDetailSerializer(ProjectEntryLabelSerializer):
    entry_count = serializers.IntegerField(read_only=True)  # Provided by ProjectEntryLabelViewSet queryset


class EntryGroupLabelSerializer(UniqueFieldsMixin, UserResourceSerializer):
    group_id = serializers.PrimaryKeyRelatedField(read_only=True)
    label_id = serializers.PrimaryKeyRelatedField(queryset=ProjectEntryLabel.objects.all())
    entry_id = serializers.PrimaryKeyRelatedField(queryset=Entry.objects.all())
    entry_client_id = serializers.CharField(source='entry.client_id', read_only=True)

    def validate(self, data):
        data['label'] = data.pop('label_id')
        data['entry'] = data.pop('entry_id')
        return data

    class Meta:
        model = EntryGroupLabel
        fields = ('id', 'label_id', 'group_id', 'entry_id', 'entry_client_id')


class LeadEntryGroupSerializer(UserResourceSerializer):
    selections = EntryGroupLabelSerializer(source='entrygrouplabel_set', many=True)

    class Meta:
        model = LeadEntryGroup
        fields = '__all__'
        read_only_fields = ('lead',)

    def validate(self, data):
        data['lead_id'] = int(self.context['view'].kwargs['lead_id'])

        # Custom validation check (It is disabled in EntryGroupLabelSerializer because of nested serializer issue)
        selections_labels = []
        for selection in self.initial_data['selections']:
            selections_label = selection['label_id']
            if selections_label in selections_labels:
                raise serializers.ValidationError('Only one entry is allowed for [Group, Label] set')
            selections_labels.append(selections_label)

        return data


class EntryLeadSerializer(RemoveNullFieldsMixin, serializers.ModelSerializer):
    attachment = FileSerializer(read_only=True)
    tabular_book = serializers.SerializerMethodField()

    assignee_details = SimpleUserSerializer(source='get_assignee', read_only=True)
    authors_detail = SimpleOrganizationSerializer(source='authors', many=True, read_only=True)
    source_detail = SimpleOrganizationSerializer(source='source', read_only=True)
    confidentiality_display = serializers.CharField(source='get_confidentiality_display', read_only=True)
    created_by_details = SimpleUserSerializer(source='get_created_by', read_only=True)
    page_count = serializers.IntegerField(
        source='leadpreview.page_count',
        read_only=True,
    )

    class Meta:
        model = Lead
        fields = (
            'id', 'title', 'created_at', 'url', 'attachment', 'tabular_book',
            'client_id', 'assignee', 'assignee_details', 'published_on',
            'authors_detail', 'source_detail', 'confidentiality_display',
            'created_by_details', 'page_count', 'confidentiality',
        )

    def get_tabular_book(self, obj):
        file = obj.attachment
        if file and hasattr(file, 'book'):
            return file.book.id
        return None


class EntrySerializer(RemoveNullFieldsMixin,
                      DynamicFieldsMixin, UserResourceSerializer):
    attributes = ListToDictField(
        child=SimpleAttributeSerializer(many=True),
        key='widget',
        source='attribute_set',
        required=False,
    )

    project = serializers.PrimaryKeyRelatedField(
        required=False,
        queryset=Project.objects.all()
    )
    resolved_comment_count = serializers.SerializerMethodField()
    unresolved_comment_count = serializers.SerializerMethodField()
    project_labels = serializers.SerializerMethodField()
    controlled_changed_by_details = SimpleUserSerializer(
        source='controlled_changed_by',
        read_only=True,
    )

    image_details = SimpleFileSerializer(source='image', read_only=True)
    lead_image = serializers.PrimaryKeyRelatedField(
        required=False,
        write_only=True,
        queryset=LeadPreviewImage.objects.all()
    )
    # NOTE: Provided by annotate `annotate_comment_count`
    verified_by_count = serializers.IntegerField(read_only=True)
    is_verified_by_current_user = serializers.BooleanField(read_only=True)

    class Meta:
        model = Entry
        fields = '__all__'

    def get_project_labels(self, entry):
        # Should be provided from view
        label_count = self.context.get('entry_group_label_count')
        if label_count is not None:
            return label_count.get(entry.pk) or []
        # Fallback
        return EntryGroupLabel.get_stat_for_entry(entry.entrygrouplabel_set)

    def get_resolved_comment_count(self, entry):
        if hasattr(entry, 'resolved_comment_count'):
            return entry.resolved_comment_count
        return entry.entrycomment_set.filter(parent=None, is_resolved=True).count()

    def get_unresolved_comment_count(self, entry):
        if hasattr(entry, 'unresolved_comment_count'):
            return entry.unresolved_comment_count
        return entry.entrycomment_set.filter(parent=None, is_resolved=False).count()

    def validate(self, data):
        """
        - Lead image is copied to deep gallery files
        - Raw image (base64) are saved as deep gallery files
        """
        request = self.context['request']
        lead = data.get('lead') or self.instance.lead
        image = data.get('image')
        image_raw = data.pop('image_raw', None)
        lead_image = data.pop('lead_image', None)

        # If gallery file is provided make sure user owns the file
        if image:
            if (
                (self.instance and self.instance.image) != image and
                not image.is_public and
                image.created_by != self.context['request'].user
            ):
                raise serializers.ValidationError({
                    'image': f'You don\'t have permission to attach image: {image}',
                })
            return data
        # If lead image is provided make sure lead are same
        elif lead_image:
            if lead_image.lead != lead:
                raise serializers.ValidationError({
                    'lead_image': f'You don\'t have permission to attach lead image: {lead_image}',
                })
            data['image'] = lead_image.clone_as_deep_file(request.user)
        elif image_raw:
            generated_image = base64_to_deep_image(
                image_raw,
                lead,
                request.user,
            )
            if type(generated_image) == File:
                data['image'] = generated_image
        return data

    def create(self, validated_data):
        if validated_data.get('project') is None:
            validated_data['project'] = validated_data['lead'].project

        return super().create(validated_data)

    def update(self, instance, validated_data):
        image = validated_data.get('image')
        if image:
            validated_data['image'] = validate_image_for_entry(
                image,
                project=validated_data['lead'].project,
                request=self.context['request'],
            )
        # once altered, uncontrol the entry if its uncontrolled
        if instance and instance.controlled:
            validated_data['controlled'] = False
            validated_data['controlled_changed_by'] = self.context['request'].user
            # NOTE: Create a review instance for this action.
            review_comment = EntryReviewComment.objects.create(
                entry=instance,
                created_by=self.context['request'].user,
                comment_type=CommentType.UNCONTROL,
            )
            review_comment.comment_texts.model.objects.create(
                comment=review_comment,
                text='This comment was generated by entry edit action'
            )
        entry = super().update(instance, validated_data)
        return entry


class EntryProccesedSerializer(EntrySerializer):
    tabular_field_data = FieldProcessedOnlySerializer(source='tabular_field')


class EntryRetriveSerializer(EntrySerializer):
    lead = EntryLeadSerializer()


class EntryRetriveProccesedSerializer(EntrySerializer):
    lead = EntryLeadSerializer()
    tabular_field_data = FieldProcessedOnlySerializer(source='tabular_field')


class EditEntriesDataSerializer(RemoveNullFieldsMixin,
                                serializers.ModelSerializer):
    lead = LeadSerializer(source='*', read_only=True)
    entries = serializers.SerializerMethodField()
    analysis_framework = AnalysisFrameworkSerializer(
        source='project.analysis_framework',
        read_only=True,
    )
    geo_options = serializers.SerializerMethodField()
    regions = SimpleRegionSerializer(
        source='project.regions', many=True, read_only=True)

    entry_labels = serializers.SerializerMethodField()
    entry_groups = serializers.SerializerMethodField()

    class Meta:
        model = Lead
        fields = (
            'lead', 'entries', 'analysis_framework', 'geo_options', 'regions',
            'entry_labels', 'entry_groups'
        )

    def get_entries(self, lead):
        return EntrySerializer(
            Entry.annotate_comment_count(lead.entry_set), many=True,
            context=self.context,
        ).data

    def get_geo_options(self, lead):
        options = {}
        for region in lead.project.regions.all():
            if not region.geo_options:
                region.calc_cache()
            options[str(region.id)] = region.geo_options
        return options

    def get_entry_labels(self, lead):
        return ProjectEntryLabelSerializer(
            ProjectEntryLabel.objects.filter(project=lead.project_id),
            many=True,
            context=self.context,
        ).data

    def get_entry_groups(self, lead):
        return LeadEntryGroupSerializer(
            LeadEntryGroup.objects.filter(lead=lead),
            many=True,
            context=self.context,
        ).data


class ComprehensiveAttributeSerializer(
        DynamicFieldsMixin,
        serializers.ModelSerializer,
):
    title = serializers.CharField(source='widget.title')
    widget_id = serializers.IntegerField(source='widget.pk')
    type = serializers.CharField(source='widget.widget_id')
    value = serializers.SerializerMethodField()

    class Meta:
        model = Attribute
        fields = ('id', 'title', 'widget_id', 'type', 'value')

    def _get_default_value(self, _, widget, data, widget_data):
        return {
            'error': 'Unsupported Widget Type, Contact Admin',
            'raw': data,
        }

    def _get_initial_wigets_meta(self, instance):
        projects_id = self.context['queryset'].order_by('project_id')\
            .values_list('project_id', flat=True).distinct()
        regions_id = Region.objects.filter(project__in=projects_id).values_list('pk', flat=True)
        geo_areas = {}
        admin_levels = {}

        geo_area_queryset = GeoArea.objects.prefetch_related('admin_level').filter(
            admin_level__region__in=regions_id,
        ).distinct()

        for geo_area in geo_area_queryset:
            geo_areas[geo_area.pk] = {
                'id': geo_area.pk,
                'title': geo_area.title,
                'pcode': geo_area.code,
                'admin_level': geo_area.admin_level_id,
                'parent': geo_area.parent_id,
            }
            if admin_levels.get(geo_area.admin_level_id) is None:
                admin_level = geo_area.admin_level
                admin_levels[geo_area.admin_level_id] = {
                    'id': admin_level.pk,
                    'level': admin_level.level,
                    'title': admin_level.title,
                }

        return {
            'geo-widget': {
                'admin_levels': admin_levels,
                'geo_areas': geo_areas,
            },
        }

    def _get_value(self, instance):
        if not hasattr(self, 'widgets_meta'):
            self.widgets_meta = self._get_initial_wigets_meta(instance)
        widget = instance.widget
        widget_data = widget.properties and widget.properties.get('data') or {}
        data = instance.data or {}
        return getattr(
            widget_store.get(instance.widget.widget_id, {}),
            'get_comprehensive_data',
            self._get_default_value,
        )(self.widgets_meta, widget, data, widget_data)

    def get_value(self, instance):
        try:
            return self._get_value(instance)
        except Exception:
            logger.warning('Comprehensive Error!! (Widget:{instance})', exc_info=True)


class ComprehensiveEntriesSerializer(
        DynamicFieldsMixin,
        serializers.ModelSerializer,
):
    tabular_field = serializers.HyperlinkedRelatedField(read_only=True, view_name='tabular_field-detail')
    attributes = ComprehensiveAttributeSerializer(source='attribute_set', many=True, read_only=True)
    created_by = ComprehensiveUserSerializer(read_only=True)
    modified_by = ComprehensiveUserSerializer(read_only=True)
    original_excerpt = serializers.CharField(source='dropped_excerpt', read_only=True)

    class Meta:
        model = Entry
        fields = (
            'id', 'created_at', 'modified_at', 'entry_type', 'excerpt', 'image_raw', 'tabular_field',
            'attributes', 'created_by', 'modified_by', 'project', 'original_excerpt',
        )


class EntryCommentTextSerializer(serializers.ModelSerializer):
    class Meta:
        model = EntryCommentText
        exclude = ('comment',)


class EntryCommentSerializer(serializers.ModelSerializer):
    created_by_detail = EntryCommentUserSerializer(source='created_by', read_only=True)
    assignees_detail = EntryCommentUserSerializer(source='assignees', read_only=True, many=True)
    text = serializers.CharField()
    lead = serializers.IntegerField(source='entry.lead_id', read_only=True)
    text_history = EntryCommentTextSerializer(
        source='entrycommenttext_set', many=True, read_only=True,
    )

    class Meta:
        model = EntryComment
        fields = '__all__'
        read_only_fields = ('entry', 'is_resolved', 'created_by', 'resolved_at')

    def _get_entry(self):
        if not hasattr(self, '_entry'):
            entry = Entry.objects.get(pk=int(self.context['entry_id']))
            self._entry = entry
        return self._entry

    def add_comment_text(self, comment, text):
        return EntryCommentText.objects.create(
            comment=comment,
            text=text,
        )

    def validate_parent(self, parent_comment):
        if parent_comment:
            if parent_comment.entry != self._get_entry():
                raise serializers.ValidationError('Selected parent comment is assigned to different entry')
            return parent_comment

    def validate(self, data):
        assignees = data.get('assignees')
        data['entry'] = entry = self._get_entry()

        # Check if all assignes are members
        if assignees:
            current_members_id = set(
                ProjectMembership.objects.filter(project=entry.project, member__in=assignees)
                .values_list('member', flat=True)
                .distinct()
            )
            assigned_users_id = set([a.id for a in assignees])
            if current_members_id != assigned_users_id:
                raise serializers.ValidationError({'assignees': "Selected assignees don't belong to this project"})

        is_patch = self.context['request'].method == 'PATCH'
        if self.instance and self.instance.is_resolved:
            raise serializers.ValidationError('Comment is resolved, no changes allowed')
        parent_comment = data.get('parent')
        if parent_comment:  # Reply comment
            if parent_comment.is_resolved:
                raise serializers.ValidationError('Parent comment is resolved, no addition allowed')
            if parent_comment.parent is not None:
                raise serializers.ValidationError('2-level of comment only allowed')
            data['entry'] = parent_comment.entry
            data['assignees'] = []
        else:  # Root comment
            if not data.get('assignees') and not is_patch:
                raise serializers.ValidationError('Root comment should have at least one assignee')
        data['created_by'] = self.context['request'].user
        return data

    def comment_save(self, validated_data, instance=None):
        """
        Comment Middleware save logic
        """
        text = validated_data.pop('text', '').strip()
        text_change = True
        if instance is None:  # Create
            instance = super().create(validated_data)
        else:  # Update
            text_change = instance.text != text
            instance = super().update(instance, validated_data)
            instance.save()
        if text and text_change:
            self.add_comment_text(instance, text)
        return instance

    def create(self, validated_data):
        return self.comment_save(validated_data)

    def update(self, instance, validated_data):
        return self.comment_save(validated_data, instance)


class SimpleEntrySerializer(serializers.ModelSerializer):
    image_details = SimpleFileSerializer(source='image', read_only=True)
    tabular_field_data = FieldProcessedOnlySerializer(source='tabular_field')

    class Meta:
        model = Entry
        fields = ('id', 'excerpt', 'dropped_excerpt',
                  'image', 'image_details', 'entry_type',
                  'tabular_field', 'tabular_field_data')


class EntryCommentTextSerializer(serializers.ModelSerializer):
    class Meta:
        exclude = ('comment',)
