import logging
from typing import Callable
from django.conf import settings
from django.shortcuts import get_object_or_404

from rest_framework import serializers
from drf_dynamic_fields import DynamicFieldsMixin
from drf_writable_nested import UniqueFieldsMixin, NestedCreateMixin
from django.db import transaction, models

from deep.graphene_context import GQLContext
from utils.graphene.fields import generate_serializer_field_class
from commons.schema_snapshots import generate_query_snapshot, SnapshotQuery
from deep.writable_nested_serializers import NestedUpdateMixin as CustomNestedUpdateMixin
from deep.serializers import (
    RemoveNullFieldsMixin,
    TempClientIdMixin,
    IntegerIDField,
    IdListField,
    GraphqlSupportDrfSerializerJSONField,
    ProjectPropertySerializerMixin,
)
from user_resource.serializers import UserResourceSerializer
from user.serializers import NanoUserSerializer
from entry.serializers import SimpleEntrySerializer
from entry.filter_set import EntryGQFilterSet, EntriesFilterDataInputType

from .models import (
    Analysis,
    AnalysisPillar,
    AnalyticalStatement,
    AnalyticalStatementEntry,
    DiscardedEntry,
    TopicModel,
    EntriesCollectionNlpTriggerBase,
    AutomaticSummary,
    AnalyticalStatementNGram,
    AnalyticalStatementGeoTask,
    # Report
    AnalysisReport,
    AnalysisReportUpload,
    AnalysisReportContainerData,
    AnalysisReportContainer,
    AnalysisReportSnapshot,
)
from .tasks import (
    trigger_topic_model,
    trigger_automatic_summary,
    trigger_automatic_ngram,
    trigger_geo_location,
)


logger = logging.getLogger(__name__)


class AnalyticalEntriesSerializer(UniqueFieldsMixin, UserResourceSerializer):
    class Meta:
        model = AnalyticalStatementEntry
        fields = ('id', 'client_id', 'order', 'entry')
        read_only_fields = ('analytical_statement',)

    def validate(self, data):
        analysis_id = self.context['view'].kwargs.get('analysis_id')
        analysis = get_object_or_404(Analysis, id=analysis_id)
        analysis_end_date = analysis.end_date
        entry = data.get('entry')
        lead_published = entry.lead.published_on
        if analysis_end_date and lead_published and lead_published > analysis_end_date:
            raise serializers.ValidationError({
                'entry': f'Entry {entry.id} lead published_on cannot be greater than analysis end_date {analysis_end_date}',
            })
        return data


class AnalyticalStatementSerializer(
    RemoveNullFieldsMixin,
    DynamicFieldsMixin,
    UserResourceSerializer,
    NestedCreateMixin,
    # XXX: This is a custom mixin where we delete first and then create to avoid duplicate key value
    CustomNestedUpdateMixin,
):
    analytical_entries = AnalyticalEntriesSerializer(source='analyticalstatemententry_set', many=True, required=False)

    class Meta:
        model = AnalyticalStatement
        fields = '__all__'
        read_only_fields = ('analysis_pillar',)

    def validate(self, data):
        analysis_pillar_id = self.context['view'].kwargs.get('analysis_pillar_id', None)
        if analysis_pillar_id:
            data['analysis_pillar_id'] = int(analysis_pillar_id)
        # Validate the analytical_entries
        entries = data.get('analyticalstatemententry_set')
        if entries and len(entries) > settings.ANALYTICAL_ENTRIES_COUNT:
            raise serializers.ValidationError(
                f'Analytical entires count must be less than {settings.ANALYTICAL_ENTRIES_COUNT}'
            )
        return data


class DiscardedEntrySerializer(serializers.ModelSerializer):
    tag_display = serializers.CharField(source='get_tag_display', read_only=True)
    entry_details = SimpleEntrySerializer(source='entry', read_only=True)

    class Meta:
        model = DiscardedEntry
        fields = '__all__'
        read_only_fields = ['analysis_pillar']

    def validate(self, data):
        data['analysis_pillar_id'] = int(self.context['analysis_pillar_id'])
        analysis_pillar = get_object_or_404(AnalysisPillar, id=data['analysis_pillar_id'])
        entry = data.get('entry')
        if entry.project != analysis_pillar.analysis.project:
            raise serializers.ValidationError('Analysis pillar project doesnot match Entry project')
        # validating the entry for the lead published_on greater than analysis end date
        analysis_end_date = analysis_pillar.analysis.end_date
        if entry.lead.published_on > analysis_end_date:
            raise serializers.ValidationError({
                'entry': f'Entry {entry.id} lead published_on cannot be greater than analysis end_date {analysis_end_date}',
            })
        return data


class AnalysisPillarSerializer(
    RemoveNullFieldsMixin,
    DynamicFieldsMixin,
    UserResourceSerializer,
):
    assignee_details = NanoUserSerializer(source='assignee', read_only=True)
    analysis_title = serializers.CharField(source='analysis.title', read_only=True)
    analytical_statements = AnalyticalStatementSerializer(many=True, source='analyticalstatement_set', required=False)

    class Meta:
        model = AnalysisPillar
        fields = '__all__'
        read_only_fields = ('analysis',)

    def validate(self, data):
        analysis_id = self.context['view'].kwargs.get('analysis_id', None)
        if analysis_id:
            data['analysis_id'] = int(analysis_id)
        # validate analysis_statement
        analytical_statement = data.get('analyticalstatement_set')
        if analytical_statement and len(analytical_statement) > settings.ANALYTICAL_STATEMENT_COUNT:
            raise serializers.ValidationError(
                f'Analytical statement count must be less than {settings.ANALYTICAL_STATEMENT_COUNT}'
            )
        return data


class AnalysisSerializer(
    RemoveNullFieldsMixin,
    DynamicFieldsMixin,
    UserResourceSerializer,
):
    analysis_pillar = AnalysisPillarSerializer(many=True, source='analysispillar_set', required=False)
    team_lead_details = NanoUserSerializer(source='team_lead', read_only=True)
    start_date = serializers.DateField(required=False, allow_null=True)

    class Meta:
        model = Analysis
        fields = '__all__'
        read_only_fields = ('project',)

    def validate(self, data):
        data['project_id'] = int(self.context['view'].kwargs['project_id'])
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        if start_date and start_date > end_date:
            raise serializers.ValidationError(
                {'end_date': 'End date must occur after start date'}
            )
        return data


class AnalysisCloneInputSerializer(serializers.Serializer):
    title = serializers.CharField(required=True, write_only=True)
    start_date = serializers.DateField(write_only=True, required=False, allow_null=True)
    end_date = serializers.DateField(required=True, write_only=True)

    def validate(self, data):
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        if start_date and start_date > end_date:
            raise serializers.ValidationError(
                {'end_date': 'End date must occur after start date'}
            )
        return data


class AnalysisSummaryPillarSerializer(serializers.ModelSerializer):
    analyzed_entries = serializers.IntegerField()
    assignee_details = NanoUserSerializer(source='assignee')

    class Meta:
        model = AnalysisPillar
        fields = ('id', 'title', 'analyzed_entries', 'assignee_details')


class AnalysisSummarySerializer(serializers.ModelSerializer):
    """
    Used with Analysis.annotate_for_analysis_summary
    """
    total_entries = serializers.IntegerField()
    total_sources = serializers.IntegerField()
    analyzed_entries = serializers.SerializerMethodField()

    publication_date = serializers.JSONField()
    team_lead_details = NanoUserSerializer(source='team_lead', read_only=True)
    pillars = AnalysisSummaryPillarSerializer(source='analysispillar_set', many=True, read_only=True)

    analyzed_sources = serializers.SerializerMethodField()

    class Meta:
        model = Analysis
        fields = (
            'id', 'title', 'team_lead', 'team_lead_details',
            'publication_date', 'pillars',
            'end_date', 'start_date',
            'analyzed_entries', 'analyzed_sources', 'total_entries',
            'total_sources', 'created_at', 'modified_at',
        )

    def get_analyzed_sources(self, analysis):
        return self.context['analyzed_sources'].get(analysis.pk)

    def get_analyzed_entries(self, analysis):
        return self.context['analyzed_entries'].get(analysis.pk)


class AnalysisPillarSummaryAnalyticalStatementSerializer(serializers.ModelSerializer):
    entries_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = AnalyticalStatement
        fields = ('id', 'statement', 'entries_count')


class AnalysisPillarSummarySerializer(serializers.ModelSerializer):
    assignee_details = NanoUserSerializer(source='assignee', read_only=True)
    analytical_statements = AnalysisPillarSummaryAnalyticalStatementSerializer(
        source='analyticalstatement_set', many=True, read_only=True)
    analyzed_entries = serializers.IntegerField(read_only=True)

    class Meta:
        model = AnalysisPillar
        fields = (
            'id', 'title', 'assignee', 'created_at',
            'assignee_details',
            'analytical_statements',
            'analyzed_entries'
        )


# ------ GRAPHQL ------------

class AnalyticalEntriesGqlSerializer(TempClientIdMixin, UniqueFieldsMixin, UserResourceSerializer):
    id = IntegerIDField(required=False)

    class Meta:
        model = AnalyticalStatementEntry
        fields = (
            'id',
            'order',
            'entry',
            'client_id',
        )

    def validate_entry(self, entry):
        if entry.project != self.context['request'].active_project:
            raise serializers.ValidationError('Invalid entry')
        return entry

    def validate(self, data):
        analysis_end_date = self.context['analysis_end_date']  # Passed by UpdateAnalysisPillar Mutation
        entry = data.get('entry')
        lead_published = entry.lead.published_on
        if analysis_end_date and lead_published and lead_published > analysis_end_date:
            raise serializers.ValidationError({
                'entry': f'Entry {entry.id} lead published_on cannot be greater than analysis end_date {analysis_end_date}',
            })
        return data


class AnalyticalStatementGqlSerializer(
    TempClientIdMixin,
    UserResourceSerializer,
    NestedCreateMixin,
    # XXX: This is a custom mixin where we delete first and then create to avoid duplicate key value
    CustomNestedUpdateMixin,
):
    id = IntegerIDField(required=False)
    entries = AnalyticalEntriesGqlSerializer(source='analyticalstatemententry_set', many=True, required=False)

    class Meta:
        model = AnalyticalStatement
        fields = (
            'id',
            'statement',
            'report_text',
            'information_gaps',
            'include_in_report',
            'order',
            'cloned_from',
            # Custom
            'entries',
            'client_id',
        )

    # NOTE: This is a custom function (apps/user_resource/serializers.py::UserResourceSerializer)
    # This makes sure only scoped (individual AnalyticalStatement) instances (entries) are updated.
    def _get_prefetch_related_instances_qs(self, qs):
        if self.instance:
            return qs.filter(analytical_statement=self.instance)
        return qs.none()  # On create throw error if existing id is provided

    def validate(self, data):
        # Validate the analytical_entries
        entries = data.get('analyticalstatemententry_set')
        if entries and len(entries) > settings.ANALYTICAL_ENTRIES_COUNT:
            raise serializers.ValidationError(
                f'Analytical entires count must be less than {settings.ANALYTICAL_ENTRIES_COUNT}'
            )
        return data


class AnalysisPillarGqlSerializer(TempClientIdMixin, UserResourceSerializer):
    statements = AnalyticalStatementGqlSerializer(many=True, source='analyticalstatement_set', required=False)

    class Meta:
        model = AnalysisPillar
        fields = (
            'title',
            'main_statement',
            'information_gap',
            'filters',
            'assignee',
            'analysis',
            'cloned_from',
            # Custom
            'statements',
            'client_id',
        )

    # NOTE: This is a custom function (apps/user_resource/serializers.py::UserResourceSerializer)
    # This makes sure only scoped (individual AnalysisPillar) instances (statements) are updated.
    # For Secondary tagging
    def _get_prefetch_related_instances_qs(self, qs):
        if self.instance:
            return qs.filter(analysis_pillar=self.instance)
        return qs.none()  # On create throw error if existing id is provided

    def validate_analysis(self, analysis):
        if analysis.project != self.context['request'].active_project:
            raise serializers.ValidationError('Invalid analysis')
        return analysis

    def validate(self, data):
        # validate analysis_statement
        analytical_statement = data.get('analyticalstatement_set')
        if analytical_statement and len(analytical_statement) > settings.ANALYTICAL_STATEMENT_COUNT:
            raise serializers.ValidationError(
                f'Analytical statement count must be less than {settings.ANALYTICAL_STATEMENT_COUNT}'
            )
        return data


class DiscardedEntryGqlSerializer(serializers.ModelSerializer):
    id = IntegerIDField(required=False)

    class Meta:
        model = DiscardedEntry
        fields = (
            'id',
            'analysis_pillar',
            'entry',
            'tag',
        )

    def validate_analysis_pillar(self, analysis_pillar):
        if analysis_pillar.analysis.project != self.context['request'].active_project:
            raise serializers.ValidationError('Invalid analysis_pillar')
        return analysis_pillar

    def validate(self, data):
        # Validate entry data but analysis_pillar is required to do so
        entry = data.get('entry')
        if entry:
            analysis_pillar = (
                self.instance.analysis_pillar if self.instance
                else data['analysis_pillar']
            )
            if entry.project != analysis_pillar.analysis.project:
                raise serializers.ValidationError('Analysis pillar project doesnot match Entry project')
            # validating the entry for the lead published_on greater than analysis end date
            analysis_end_date = analysis_pillar.analysis.end_date
            if entry.lead.published_on > analysis_end_date:
                raise serializers.ValidationError({
                    'entry': (
                        f'Entry {entry.id} lead published_on cannot be greater than analysis end_date {analysis_end_date}'
                    ),
                })
        return data


class AnalysisGqlSerializer(UserResourceSerializer):
    id = IntegerIDField(required=False)
    analysis_pillar = AnalysisPillarGqlSerializer(many=True, source='analysispillar_set', required=False)
    start_date = serializers.DateField(required=False, allow_null=True)

    class Meta:
        model = Analysis
        fields = (
            'id',
            'title',
            'team_lead',
            'project',
            'start_date',
            'end_date',
            'cloned_from',
        )

    def validate_project(self, project):
        if project != self.context['request'].active_project:
            raise serializers.ValidationError('Invalid project')
        return project

    def validate(self, data):
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        if start_date and start_date > end_date:
            raise serializers.ValidationError(
                {'end_date': 'End date must occur after start date'}
            )
        return data


AnalysisCloneGqlSerializer = AnalysisCloneInputSerializer


class AnalysisTopicModelSerializer(UserResourceSerializer, serializers.ModelSerializer):
    additional_filters = generate_serializer_field_class(
        EntriesFilterDataInputType,
        GraphqlSupportDrfSerializerJSONField,
    )(required=False)

    class Meta:
        model = TopicModel
        fields = (
            'analysis_pillar',
            'additional_filters',
        )

    def validate_analysis_pillar(self, analysis_pillar):
        if analysis_pillar.analysis.project != self.context['request'].active_project:
            raise serializers.ValidationError('Invalid analysis pillar')
        return analysis_pillar

    def validate_additional_filters(self, additional_filters):
        filter_set = EntryGQFilterSet(data=additional_filters, request=self.context['request'])
        if not filter_set.is_valid():
            raise serializers.ValidationError(filter_set.errors)
        return additional_filters

    def create(self, data):
        if not TopicModel._get_entries_qs(
                data['analysis_pillar'],
                data.get('additional_filters') or {},
        ).exists():
            raise serializers.ValidationError('No entries found to process')
        instance = super().create(data)
        transaction.on_commit(
            lambda: trigger_topic_model.delay(instance.pk)
        )
        return instance


class EntriesCollectionNlpTriggerBaseSerializer(UserResourceSerializer, serializers.ModelSerializer):
    entries_id = IdListField()
    trigger_task_func: Callable

    class Meta:
        model = EntriesCollectionNlpTriggerBase
        fields = (
            'entries_id',
        )

    def validate_entries_id(self, entries_id):
        entries_id = self.Meta.model.get_valid_entries_id(
            self.context['request'].active_project.id,
            entries_id
        )
        if not entries_id:
            raise serializers.ValidationError('No entries found to process')
        return entries_id

    def create(self, data):
        data['project'] = self.context['request'].active_project
        existing_instance = self.Meta.model.get_existing(data['entries_id'])
        if existing_instance:
            return existing_instance
        instance = super().create(data)
        transaction.on_commit(
            lambda: self.trigger_task_func.delay(instance.pk)
        )
        return instance

    def update(self, _):
        raise serializers.ValidationError('Not allowed using this serializer.')


class AnalysisAutomaticSummarySerializer(EntriesCollectionNlpTriggerBaseSerializer):
    trigger_task_func = trigger_automatic_summary

    class Meta:
        model = AutomaticSummary
        fields = (
            'entries_id',
        )


class AnalyticalStatementNGramSerializer(EntriesCollectionNlpTriggerBaseSerializer):
    trigger_task_func = trigger_automatic_ngram

    class Meta:
        model = AnalyticalStatementNGram
        fields = (
            'entries_id',
        )


class AnalyticalStatementGeoTaskSerializer(EntriesCollectionNlpTriggerBaseSerializer):
    trigger_task_func = trigger_geo_location

    class Meta:
        model = AnalyticalStatementGeoTask
        fields = (
            'entries_id',
        )


# ReportModule
class ReportEnum:
    class VariableType(models.TextChoices):
        TEXT = 'text'
        NUMBER = 'number'
        DATE = 'date'

    class TextStypeAlign(models.TextChoices):
        START = 'start'
        END = 'end'
        CENTER = 'center'
        JUSTIFIED = 'justified'

    class BorderStyleStype(models.TextChoices):
        DOTTED = 'dotted'
        DASHED = 'dashed'
        SOLID = 'solid'
        DOUBLE = 'double'
        NONE = 'none'

    class ImageContentStyleFit(models.TextChoices):
        FILL = 'fill'
        CONTAIN = 'contain'
        COVER = 'cover'
        SCALE_DOWN = 'scale-down'
        NONE = 'none'

    class HeadingConfigurationVariant(models.TextChoices):
        H1 = 'h1'
        H2 = 'h2'
        H3 = 'h3'
        H4 = 'h4'


class AnalysisReportVariableSerializer(serializers.Serializer):
    name = serializers.CharField(required=False)
    type = serializers.ChoiceField(choices=ReportEnum.VariableType.choices, required=False)
    completeness = serializers.IntegerField(required=False)


class AnalysisReportTextStyleSerializer(serializers.Serializer):
    color = serializers.CharField(required=False)
    family = serializers.CharField(required=False)
    size = serializers.IntegerField(required=False)
    weight = serializers.IntegerField(required=False)
    align = serializers.ChoiceField(choices=ReportEnum.TextStypeAlign.choices, required=False)


class AnalysisReportMarginStyleSerializer(serializers.Serializer):
    top = serializers.IntegerField(required=False)
    bottom = serializers.IntegerField(required=False)
    left = serializers.IntegerField(required=False)
    right = serializers.IntegerField(required=False)


class AnalysisReportPaddingStyleSerializer(serializers.Serializer):
    top = serializers.IntegerField(required=False)
    bottom = serializers.IntegerField(required=False)
    left = serializers.IntegerField(required=False)
    right = serializers.IntegerField(required=False)


class AnalysisReportBorderStyleSerializer(serializers.Serializer):
    color = serializers.CharField(required=False)
    width = serializers.IntegerField(required=False)
    opacity = serializers.IntegerField(required=False)
    style = serializers.ChoiceField(choices=ReportEnum.BorderStyleStype.choices, required=False)


class AnalysisReportBackgroundStyleSerializer(serializers.Serializer):
    color = serializers.CharField(required=False)
    opacity = serializers.IntegerField(required=False)


class AnalysisReportPageStyleSerializer(serializers.Serializer):
    margin = AnalysisReportMarginStyleSerializer(required=False)
    background = AnalysisReportBackgroundStyleSerializer(required=False)


class AnalysisReportHeaderStyleSerializer(serializers.Serializer):
    padding = AnalysisReportPaddingStyleSerializer(required=False)
    border = AnalysisReportBorderStyleSerializer(required=False)
    background = AnalysisReportBackgroundStyleSerializer(required=False)

    title = AnalysisReportTextStyleSerializer(required=False)
    subTitle = AnalysisReportTextStyleSerializer(required=False)


class AnalysisReportBodyStyleSerializer(serializers.Serializer):
    gap = serializers.IntegerField(required=False)


class AnalysisReportContainerStyleSerializer(serializers.Serializer):
    padding = AnalysisReportPaddingStyleSerializer(required=False)
    border = AnalysisReportBorderStyleSerializer(required=False)
    background = AnalysisReportBackgroundStyleSerializer(required=False)


class AnalysisReportTextContentStyleSerializer(serializers.Serializer):
    content = AnalysisReportTextStyleSerializer(required=False)


class AnalysisReportHeadingContentStyleSerializer(serializers.Serializer):
    h1 = AnalysisReportTextStyleSerializer(required=False)
    h2 = AnalysisReportTextStyleSerializer(required=False)
    h3 = AnalysisReportTextStyleSerializer(required=False)
    h4 = AnalysisReportTextStyleSerializer(required=False)


class AnalysisReportImageContentStyleSerializer(serializers.Serializer):
    caption = AnalysisReportTextStyleSerializer(required=False)
    fit = serializers.ChoiceField(choices=ReportEnum.ImageContentStyleFit.choices, required=False)


class AnalysisReportUrlContentStyleSerializer(serializers.Serializer):
    # TODO: Define fields here
    noop = serializers.CharField(required=False)


# XXX: NOT USED
class AnalysisReportTextConfigurationSerializer(serializers.Serializer):
    content = serializers.CharField(required=False)
    content_style = AnalysisReportTextContentStyleSerializer(required=False)


# XXX: NOT USED
class AnalysisReportHeadingConfigurationSerializer(serializers.Serializer):
    content = serializers.CharField(required=False)
    content_style = AnalysisReportTextContentStyleSerializer(required=False)
    variant = serializers.ChoiceField(choices=ReportEnum.HeadingConfigurationVariant.choices, required=False)


class AnalysisReportUrlConfigurationSerializer(serializers.Serializer):
    url = serializers.CharField(required=False)


class AnalysisReportImageConfigurationSerializer(serializers.Serializer):
    caption = serializers.CharField(required=False)
    altText = serializers.CharField(required=False)


class AnalysisReportConfigurationSerializer(serializers.Serializer):
    # Configuration for page
    page_style = AnalysisReportPageStyleSerializer(required=False)
    # Configuration for page header
    header_style = AnalysisReportHeaderStyleSerializer(required=False)
    # Configuration for page body
    body_style = AnalysisReportBodyStyleSerializer(required=False)
    # -- Default Configuration for
    # Container
    container_style = AnalysisReportContainerStyleSerializer(required=False)
    # Text content
    text_content_style = AnalysisReportTextContentStyleSerializer(required=False)
    # Heading content
    heading_content_style = AnalysisReportHeadingContentStyleSerializer(required=False)
    # Image content
    image_content_style = AnalysisReportImageContentStyleSerializer(required=False)
    # URL content
    url_content_style = AnalysisReportUrlConfigurationSerializer(required=False)


class AnalysisReportContainerContentStyleSerializer(serializers.Serializer):
    text = AnalysisReportTextContentStyleSerializer(required=False)
    heading = AnalysisReportHeaderStyleSerializer(required=False)
    image = AnalysisReportImageContentStyleSerializer(required=False)
    url = AnalysisReportUrlContentStyleSerializer(required=False)


class AnalysisReportContainerContentConfigurationSerializer(serializers.Serializer):
    text = AnalysisReportTextConfigurationSerializer(required=False)
    heading = AnalysisReportHeadingConfigurationSerializer(required=False)
    image = AnalysisReportImageConfigurationSerializer(required=False)
    url = AnalysisReportUrlConfigurationSerializer(required=False)


class AnalysisReportContainerDataSerializer(serializers.ModelSerializer):
    id = IntegerIDField(required=False)

    class Meta:
        model = AnalysisReportContainerData
        fields = (
            'id',
            'upload',  # TODO Validation
            'data',
        )


class AnalysisReportContainerSerializer(NestedCreateMixin, serializers.ModelSerializer):
    id = IntegerIDField(required=False)

    class Meta:
        model = AnalysisReportContainer
        fields = (
            'id',
            'row',
            'column',
            'width',
            'height',
            'content_type',
            # Custom
            'style',
            'content_style',
            'content_configuration',
            'content_data',
        )

    style = AnalysisReportContainerStyleSerializer(required=False)

    # Content metadata
    content_style = AnalysisReportContainerContentStyleSerializer(required=False)
    content_configuration = AnalysisReportContainerContentConfigurationSerializer(required=False)

    # TODO: Model Field, Nested Serializer
    content_data = AnalysisReportContainerDataSerializer(many=True, source='analysisreportcontainerdata_set')


class AnalysisReportSerializer(UserResourceSerializer):
    class Meta:
        model = AnalysisReport
        fields = (
            'analysis',  # TODO Validation
            'slug',
            'title',
            'sub_title',
            'is_public',
            'organizations',
            # Custom
            'configuration',
            'containers',
        )

    configuration = AnalysisReportConfigurationSerializer(required=False)
    containers = AnalysisReportContainerSerializer(many=True, source='analysisreportcontainer_set')


# -- Snapshot
class AnalysisReportSnapshotSerializer(ProjectPropertySerializerMixin, serializers.ModelSerializer):
    class Meta:
        model = AnalysisReportSnapshot
        fields = (
            'report',
        )

    serializers.FileField()

    def validate_report(self, report):
        if self.project.id != report.analysis.project_id:
            raise serializers.ValidationError('Invalid report')
        return report

    def validate(self, data):
        report = data['report']
        snaphost_file, errors = generate_query_snapshot(
            SnapshotQuery.AnalysisReport.Snapshot,
            {
                'projectID': str(self.project.id),
                'reportID': str(report.id),
            },
            data_callback=lambda x: x['project']['analysisReport'],
            context=GQLContext(self.context['request']),
        )
        if snaphost_file is None:
            logger.error(
                f'Failed to generate snapshot for report-pk: {report.id}',
                extra={'context': errors}
            )
            raise serializers.ValidationError('Failed to generate snapshot')
        data['report_data_file'] = snaphost_file
        data['published_by'] = self.context['request'].user
        return data

    def create(self, data):
        instance = super().create(data)
        # Save file
        instance.report_data_file.save(f'{instance.report.id}-{instance.report.slug}.json', data['report_data_file'])
        return instance

    def update(self, _):
        raise Exception('Not implemented')


# -- Uploads
# -- -- Metadata
class AnalysisReportUploadMetadataXlsxSheetSerializer(serializers.Serializer):
    name = serializers.CharField(required=False)
    header_row = serializers.IntegerField(required=False)
    variables = AnalysisReportVariableSerializer(many=True)


class AnalysisReportUploadMetadataXlsxSerializer(serializers.Serializer):
    sheets = AnalysisReportUploadMetadataXlsxSheetSerializer(many=True)


class AnalysisReportUploadMetadataCsvSerializer(serializers.Serializer):
    header_row = serializers.IntegerField(required=False)
    variables = AnalysisReportVariableSerializer(many=True)


class AnalysisReportUploadMetadataGeoJsonSerializer(serializers.Serializer):
    variables = AnalysisReportVariableSerializer(many=True)


class AnalysisReportUploadMetadataSerializer(serializers.Serializer):
    xlsx = AnalysisReportUploadMetadataXlsxSerializer()
    csv = AnalysisReportUploadMetadataCsvSerializer()
    geojson = AnalysisReportUploadMetadataGeoJsonSerializer()
    # image = AnalysisReportUploadMetadataGeoJsonSerializer()


# TODO: Seperate mutation
class AnalysisReportUploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnalysisReportUpload
        fields = (
            'id',
            'report',  # TODO Validation
            'file',  # TODO Validation
            'type',
            # Custom
            'metadata',
        )

    metadata = AnalysisReportUploadMetadataSerializer(required=False)
    # TODO Validations
