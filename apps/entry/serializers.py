from drf_dynamic_fields import DynamicFieldsMixin
from rest_framework import serializers

from deep.serializers import (
    RemoveNullFieldsMixin,
    ListToDictField,
)
from project.serializers import ProjectEntitySerializer
from project.models import Project
from lead.serializers import LeadSerializer, LegacyLeadSerializer
from lead.models import Lead
from analysis_framework.serializers import AnalysisFrameworkSerializer
from geo.models import GeoArea, Region
from geo.serializers import SimpleRegionSerializer
from tabular.serializers import FieldProcessedOnlySerializer
from user.serializers import ComprehensiveUserSerializer
from .widgets.store import widget_store

from .models import (
    Attribute,
    Entry,
    EntryComment,
    EntryCommentText,
    ExportData,
    FilterData,
)
from .utils import validate_image_for_entry


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


class EntryLeadSerializer(RemoveNullFieldsMixin, serializers.ModelSerializer):
    class Meta:
        model = Lead
        fields = ('id', 'title', 'created_at',)


class EntrySerializer(RemoveNullFieldsMixin,
                      DynamicFieldsMixin, ProjectEntitySerializer):
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

    class Meta:
        model = Entry
        fields = '__all__'

    def get_resolved_comment_count(self, entry):
        return getattr(
            entry, 'resolved_comment_count',
            entry.entrycomment_set.filter(parent=None, is_resolved=True).count()
        )

    def get_unresolved_comment_count(self, entry):
        return getattr(
            entry, 'unresolved_comment_count',
            entry.entrycomment_set.filter(parent=None, is_resolved=False).count()
        )

    def create(self, validated_data):
        if validated_data.get('project') is None:
            validated_data['project'] = validated_data['lead'].project

        image = validated_data.get('image')
        if image:
            validated_data['image'] = validate_image_for_entry(
                image,
                project=validated_data['lead'].project,
                request=self.context['request'],
            )

        return super().create(validated_data)

    def update(self, instance, validated_data):
        image = validated_data.get('image')
        if image:
            validated_data['image'] = validate_image_for_entry(
                image,
                project=validated_data['lead'].project,
                request=self.context['request'],
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
    regions = SimpleRegionSerializer(source='project.regions', many=True,
                                     read_only=True)

    class Meta:
        model = Lead
        fields = ('lead', 'entries', 'analysis_framework', 'geo_options',
                  'regions')

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


class LegacyEditEntriesDataSerializer(EditEntriesDataSerializer):
    lead = LegacyLeadSerializer(source='*', read_only=True)


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

    def get_value(self, instance):
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


class ComprehensiveEntriesSerializer(
        DynamicFieldsMixin,
        serializers.ModelSerializer,
):
    tabular_field = serializers.HyperlinkedRelatedField(read_only=True, view_name='tabular_field-detail')
    attributes = ComprehensiveAttributeSerializer(source='attribute_set', many=True, read_only=True)
    created_by = ComprehensiveUserSerializer()
    modified_by = ComprehensiveUserSerializer()

    class Meta:
        model = Entry
        fields = (
            'id', 'created_at', 'modified_at', 'entry_type', 'excerpt', 'image', 'tabular_field',
            'attributes', 'created_by', 'modified_by', 'project',
        )


class EntryCommentTextSerializer(serializers.ModelSerializer):
    class Meta:
        model = EntryCommentText
        exclude = ('comment',)


class EntryCommentSerializer(serializers.ModelSerializer):
    created_by_detail = ComprehensiveUserSerializer(source='created_by', read_only=True)
    assignee_detail = ComprehensiveUserSerializer(source='assignee', read_only=True)
    text = serializers.CharField()
    lead = serializers.IntegerField(source='entry.lead_id', read_only=True)
    text_history = EntryCommentTextSerializer(
        source='entrycommenttext_set', many=True, read_only=True,
    )

    class Meta:
        model = EntryComment
        fields = '__all__'
        read_only_fields = ('is_resolved', 'created_by', 'resolved_at')

    def add_comment_text(self, comment, text):
        return EntryCommentText.objects.create(
            comment=comment,
            text=text,
        )

    def validate(self, data):
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
            data['assignee'] = None
        else:  # Root comment
            if data.get('assignee') is None and not is_patch:
                raise serializers.ValidationError('Root comment should have assignee')
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
