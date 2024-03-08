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


# -------------------------- ReportModule --------------------------------
class ReportEnum:
    class VariableType(models.TextChoices):
        TEXT = 'text'
        NUMBER = 'number'
        DATE = 'date'
        BOOLEAN = 'boolean'

    class TextStyleAlign(models.TextChoices):
        START = 'start'
        END = 'end'
        CENTER = 'center'
        JUSTIFIED = 'justified'

    class BorderStyleStyle(models.TextChoices):
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

    class HorizontalAxisType(models.TextChoices):
        CATEGORICAL = 'categorical'
        NUMERIC = 'numeric'
        DATE = 'date'

    class BarChartType(models.TextChoices):
        SIDE_BY_SIDE = 'side-by-side'
        STACKED = 'stacked'

    class BarChartDirection(models.TextChoices):
        VERTICAL = 'vertical'
        HORIZONTAL = 'horizontal'

    class LegendPosition(models.TextChoices):
        TOP = 'top'
        LEFT = 'left'
        BOTTOM = 'bottom'
        RIGHT = 'right'

    class LegendDotShape(models.TextChoices):
        CIRCLE = 'circle'
        TRIANGLE = 'triangle'
        SQUARE = 'square'
        DIAMOND = 'diamond'

    class AggregationType(models.TextChoices):
        COUNT = 'count'
        SUM = 'sum'
        MEAN = 'mean'
        MEDIAN = 'median'
        MIN = 'min'
        MAX = 'max'

    class MapLayerType(models.TextChoices):
        OSM_LAYER = 'OSM Layer'
        MAPBOX_LAYER = 'Mapbox Layer'
        SYMBOL_LAYER = 'Symbol Layer'
        POLYGON_LAYER = 'Polygon Layer'
        LINE_LAYER = 'Line Layer'
        HEAT_MAP_LAYER = 'Heatmap Layer'


class AnalysisReportVariableSerializer(serializers.Serializer):
    name = serializers.CharField(required=False, allow_null=True)
    client_id = serializers.CharField(required=False)
    type = serializers.ChoiceField(choices=ReportEnum.VariableType.choices, required=False, allow_null=True)
    completeness = serializers.IntegerField(required=False, allow_null=True)


class AnalysisReportTextStyleSerializer(serializers.Serializer):
    color = serializers.CharField(required=False, allow_null=True)
    family = serializers.CharField(required=False, allow_null=True)
    size = serializers.IntegerField(required=False, allow_null=True)
    weight = serializers.IntegerField(required=False, allow_null=True)
    align = serializers.ChoiceField(choices=ReportEnum.TextStyleAlign.choices, required=False, allow_null=True)


class AnalysisReportMarginStyleSerializer(serializers.Serializer):
    top = serializers.IntegerField(required=False, allow_null=True)
    bottom = serializers.IntegerField(required=False, allow_null=True)
    left = serializers.IntegerField(required=False, allow_null=True)
    right = serializers.IntegerField(required=False, allow_null=True)


class AnalysisReportPaddingStyleSerializer(serializers.Serializer):
    top = serializers.IntegerField(required=False, allow_null=True)
    bottom = serializers.IntegerField(required=False, allow_null=True)
    left = serializers.IntegerField(required=False, allow_null=True)
    right = serializers.IntegerField(required=False, allow_null=True)


class AnalysisReportBorderStyleSerializer(serializers.Serializer):
    color = serializers.CharField(required=False, allow_null=True)
    width = serializers.IntegerField(required=False, allow_null=True)
    opacity = serializers.IntegerField(required=False, allow_null=True)
    style = serializers.ChoiceField(choices=ReportEnum.BorderStyleStyle.choices, required=False)


class AnalysisReportBackgroundStyleSerializer(serializers.Serializer):
    color = serializers.CharField(required=False, allow_null=True)
    opacity = serializers.IntegerField(required=False, allow_null=True)


class AnalysisReportPageStyleSerializer(serializers.Serializer):
    margin = AnalysisReportMarginStyleSerializer(required=False, allow_null=True)
    background = AnalysisReportBackgroundStyleSerializer(required=False, allow_null=True)


class AnalysisReportHeaderStyleSerializer(serializers.Serializer):
    padding = AnalysisReportPaddingStyleSerializer(required=False, allow_null=True)
    border = AnalysisReportBorderStyleSerializer(required=False, allow_null=True)
    background = AnalysisReportBackgroundStyleSerializer(required=False, allow_null=True)

    title = AnalysisReportTextStyleSerializer(required=False, allow_null=True)
    subTitle = AnalysisReportTextStyleSerializer(required=False, allow_null=True)


class AnalysisReportBodyStyleSerializer(serializers.Serializer):
    gap = serializers.IntegerField(required=False, allow_null=True)


class AnalysisReportContainerStyleSerializer(serializers.Serializer):
    padding = AnalysisReportPaddingStyleSerializer(required=False, allow_null=True)
    border = AnalysisReportBorderStyleSerializer(required=False, allow_null=True)
    background = AnalysisReportBackgroundStyleSerializer(required=False, allow_null=True)


class AnalysisReportTextContentStyleSerializer(serializers.Serializer):
    content = AnalysisReportTextStyleSerializer(required=False, allow_null=True)


class AnalysisReportHeadingConfigurationStyleSerializer(serializers.Serializer):
    content = AnalysisReportTextStyleSerializer(required=False, allow_null=True)


class AnalysisReportHeadingContentStyleSerializer(serializers.Serializer):
    h1 = AnalysisReportTextStyleSerializer(required=False, allow_null=True)
    h2 = AnalysisReportTextStyleSerializer(required=False, allow_null=True)
    h3 = AnalysisReportTextStyleSerializer(required=False, allow_null=True)
    h4 = AnalysisReportTextStyleSerializer(required=False, allow_null=True)


class AnalysisReportImageContentStyleSerializer(serializers.Serializer):
    caption = AnalysisReportTextStyleSerializer(required=False, allow_null=True)
    fit = serializers.ChoiceField(choices=ReportEnum.ImageContentStyleFit.choices, required=False, allow_null=True)


class AnalysisReportTextConfigurationSerializer(serializers.Serializer):
    content = serializers.CharField(required=False, allow_null=True)
    style = AnalysisReportTextContentStyleSerializer(required=False, allow_null=True)


class AnalysisReportHeadingConfigurationSerializer(serializers.Serializer):
    content = serializers.CharField(required=False, allow_null=True)
    style = AnalysisReportHeadingConfigurationStyleSerializer(required=False, allow_null=True)
    variant = serializers.ChoiceField(choices=ReportEnum.HeadingConfigurationVariant.choices, required=False)


class AnalysisReportUrlConfigurationSerializer(serializers.Serializer):
    url = serializers.CharField(required=False, allow_null=True)


class AnalysisReportKpiItemStyleConfigurationSerializer(serializers.Serializer):
    title_content_style = AnalysisReportTextStyleSerializer(required=False, allow_null=True)
    subtitle_content_style = AnalysisReportTextStyleSerializer(required=False, allow_null=True)
    source_content_style = AnalysisReportTextStyleSerializer(required=False, allow_null=True)
    value_content_style = AnalysisReportTextStyleSerializer(required=False, allow_null=True)


class AnalysisReportKpiItemConfigurationSerializer(serializers.Serializer):
    title = serializers.CharField(required=False, allow_null=True)
    subtitle = serializers.CharField(required=False, allow_null=True)
    source = serializers.CharField(required=False, allow_null=True)
    source_url = serializers.CharField(required=False, allow_null=True)
    color = serializers.CharField(required=False, allow_null=True)
    date = serializers.DateField(required=False, allow_null=True)
    value = serializers.IntegerField(required=False, allow_null=True)
    client_id = serializers.CharField(required=False, allow_null=True)
    abbreviate_value = serializers.BooleanField(required=False, allow_null=True)
    style = AnalysisReportKpiItemStyleConfigurationSerializer(required=False, allow_null=True)

    def validate_date(self, date):
        if date:
            return date.isoformat()


class AnalysisReportCategoricalLegendStyleSerializer(serializers.Serializer):
    position = serializers.ChoiceField(choices=ReportEnum.LegendPosition.choices, required=False, allow_null=True)
    shape = serializers.ChoiceField(choices=ReportEnum.LegendDotShape.choices, required=False, allow_null=True)
    heading = AnalysisReportTextStyleSerializer(required=False, allow_null=True)
    label = AnalysisReportTextStyleSerializer(required=False, allow_null=True)


class AnalysisReportBarStyleSerializer(serializers.Serializer):
    border = AnalysisReportBorderStyleSerializer(required=False, allow_null=True)


class AnalysisReportGridLineStyleSerializer(serializers.Serializer):
    line_color = serializers.CharField(required=False, allow_null=True)
    line_width = serializers.IntegerField(required=False, allow_null=True)
    line_opacity = serializers.IntegerField(required=False, allow_null=True)


class AnalysisReportTickStyleSerializer(serializers.Serializer):
    line_color = serializers.CharField(required=False, allow_null=True)
    line_width = serializers.IntegerField(required=False, allow_null=True)
    line_opacity = serializers.IntegerField(required=False, allow_null=True)


class AnalysisReportBarChartStyleSerializer(serializers.Serializer):
    title = AnalysisReportTextStyleSerializer(required=False, allow_null=True)
    sub_title = AnalysisReportTextStyleSerializer(required=False, allow_null=True)
    legend = AnalysisReportCategoricalLegendStyleSerializer(required=False, allow_null=True)
    bar = AnalysisReportBarStyleSerializer(required=False, allow_null=True)

    horizontal_axis_title = AnalysisReportTextStyleSerializer(required=False, allow_null=True)
    vertical_axis_title = AnalysisReportTextStyleSerializer(required=False, allow_null=True)
    horizontal_axis_tick_label = AnalysisReportTextStyleSerializer(required=False, allow_null=True)
    vertical_axis_tick_label = AnalysisReportTextStyleSerializer(required=False, allow_null=True)

    vertical_grid_line = AnalysisReportGridLineStyleSerializer(required=False, allow_null=True)
    horizontal_grid_line = AnalysisReportGridLineStyleSerializer(required=False, allow_null=True)
    vertical_tick = AnalysisReportTickStyleSerializer(required=False, allow_null=True)
    horizontal_tick = AnalysisReportTickStyleSerializer(required=False, allow_null=True)


class AnalysisReportHorizontalAxisSerializer(serializers.Serializer):
    field = serializers.CharField(required=False, allow_null=True)
    type = serializers.ChoiceField(choices=ReportEnum.HorizontalAxisType.choices, required=False, allow_null=True)


class AnalysisReportVerticalAxisSerializer(serializers.Serializer):
    client_id = serializers.CharField(required=False)
    label = serializers.CharField(required=False)
    field = serializers.CharField(required=False, allow_null=True)
    aggregation_type = serializers.ChoiceField(choices=ReportEnum.AggregationType.choices, required=False, allow_null=True)
    color = serializers.CharField(required=False, allow_null=True)


class AnalysisReportBarChartConfigurationSerializer(serializers.Serializer):
    sheet = serializers.CharField(required=False, allow_null=True)
    type = serializers.ChoiceField(choices=ReportEnum.BarChartType.choices, required=True)
    direction = serializers.ChoiceField(choices=ReportEnum.BarChartDirection.choices, required=True)

    horizontal_axis = AnalysisReportHorizontalAxisSerializer(required=True)
    vertical_axis = AnalysisReportVerticalAxisSerializer(many=True)

    horizontal_axis_title = serializers.CharField(required=False, allow_null=True)
    vertical_axis_title = serializers.CharField(required=False, allow_null=True)

    title = serializers.CharField(required=False, allow_null=True)
    sub_title = serializers.CharField(required=False, allow_null=True)

    legend_heading = serializers.CharField(required=False, allow_null=True)

    horizontal_tick_label_rotation = serializers.IntegerField(required=False, allow_null=True)
    horizontal_axis_line_visible = serializers.BooleanField(required=False, allow_null=True)
    vertical_axis_line_visible = serializers.BooleanField(required=False, allow_null=True)
    vertical_axis_extend_minimum_value = serializers.IntegerField(required=False, allow_null=True)
    vertical_axis_extend_maximum_value = serializers.IntegerField(required=False, allow_null=True)
    vertical_grid_line_visible = serializers.BooleanField(required=False, allow_null=True)
    horizontal_grid_line_visible = serializers.BooleanField(required=False, allow_null=True)
    vertical_tick_visible = serializers.BooleanField(required=False, allow_null=True)
    horizontal_tick_visible = serializers.BooleanField(required=False, allow_null=True)

    style = AnalysisReportBarChartStyleSerializer(required=False, allow_null=True)


class AnalysisReportTimelineChartConfigurationSerializer(serializers.Serializer):
    sheet = serializers.CharField(required=False, allow_null=True)
    date = serializers.CharField(required=True)
    title = serializers.CharField(required=True)
    detail = serializers.CharField(required=False, allow_null=True)
    category = serializers.CharField(required=False, allow_null=True)
    source = serializers.CharField(required=False, allow_null=True)
    source_url = serializers.CharField(required=False, allow_null=True)


class AnalysisReportKpiConfigurationSerializer(serializers.Serializer):
    items = AnalysisReportKpiItemConfigurationSerializer(many=True)
    title_content_style = AnalysisReportTextStyleSerializer(required=False, allow_null=True)
    subtitle_content_style = AnalysisReportTextStyleSerializer(required=False, allow_null=True)
    source_content_style = AnalysisReportTextStyleSerializer(required=False, allow_null=True)
    value_content_style = AnalysisReportTextStyleSerializer(required=False, allow_null=True)


class AnalysisReportImageConfigurationSerializer(serializers.Serializer):
    caption = serializers.CharField(required=False, allow_null=True)
    altText = serializers.CharField(required=False, allow_null=True)
    style = AnalysisReportImageContentStyleSerializer(required=False, allow_null=True)


class AnalysisReportConfigurationSerializer(serializers.Serializer):
    # Configuration for page
    page_style = AnalysisReportPageStyleSerializer(required=False, allow_null=True)
    # Configuration for page header
    header_style = AnalysisReportHeaderStyleSerializer(required=False, allow_null=True)
    # Configuration for page body
    body_style = AnalysisReportBodyStyleSerializer(required=False, allow_null=True)
    # -- Default Configuration for
    # Container
    container_style = AnalysisReportContainerStyleSerializer(required=False, allow_null=True)
    # Text content
    text_content_style = AnalysisReportTextContentStyleSerializer(required=False, allow_null=True)
    # Heading content
    heading_content_style = AnalysisReportHeadingContentStyleSerializer(required=False, allow_null=True)
    # Image content
    image_content_style = AnalysisReportImageContentStyleSerializer(required=False, allow_null=True)
    # URL content
    url_content_style = AnalysisReportUrlConfigurationSerializer(required=False, allow_null=True)


class AnalysisReportMapboxLayerConfigurationSerializer(serializers.Serializer):
    mapbox_style = serializers.CharField(required=False, allow_null=True)


class AnalysisReportLineLayerConfigurationSerializer(serializers.Serializer):
    # NOTE: This reference will be handled in frontend
    upload_id = serializers.CharField(required=True)
    label_column = serializers.CharField(required=True)
    show_labels = serializers.BooleanField(required=False, allow_null=True)
    show_in_legend = serializers.BooleanField(required=False, allow_null=True)


class AnalysisReportSymbolLayerConfigurationSerializer(serializers.Serializer):
    # NOTE: This reference will be handled in frontend
    upload_id = serializers.CharField(required=True)
    label_column = serializers.CharField(required=True)


class AnalysisReportPolygonLayerConfigurationSerializer(serializers.Serializer):
    # NOTE: This reference will be handled in frontend
    upload_id = serializers.CharField(required=True)
    label_column = serializers.CharField(required=True)


class AnalysisReportLayerConfigSerializer(serializers.Serializer):
    mapbox_layer = AnalysisReportMapboxLayerConfigurationSerializer(required=False, allow_null=True)
    line_layer = AnalysisReportLineLayerConfigurationSerializer(required=False, allow_null=True)
    symbol_layer = AnalysisReportSymbolLayerConfigurationSerializer(required=False, allow_null=True)
    polygon_layer = AnalysisReportPolygonLayerConfigurationSerializer(required=False, allow_null=True)


class AnalysisReportMapLayerConfigurationSerializer(serializers.Serializer):
    client_id = serializers.CharField(required=True)
    name = serializers.CharField(required=True)
    visible = serializers.CharField(required=True)
    order = serializers.IntegerField(required=True)
    opacity = serializers.IntegerField(required=False, allow_null=True)
    type = serializers.ChoiceField(choices=ReportEnum.MapLayerType.choices, required=False, allow_null=True)
    layer_config = AnalysisReportLayerConfigSerializer(required=False, allow_null=True)


class AnalysisReportMapConfigurationSerializer(serializers.Serializer):
    layers = AnalysisReportMapLayerConfigurationSerializer(many=True)


class AnalysisReportContainerContentConfigurationSerializer(serializers.Serializer):
    text = AnalysisReportTextConfigurationSerializer(required=False, allow_null=True)
    heading = AnalysisReportHeadingConfigurationSerializer(required=False, allow_null=True)
    image = AnalysisReportImageConfigurationSerializer(required=False, allow_null=True)
    url = AnalysisReportUrlConfigurationSerializer(required=False, allow_null=True)
    kpi = AnalysisReportKpiConfigurationSerializer(required=False, allow_null=True)
    bar_chart = AnalysisReportBarChartConfigurationSerializer(required=False, allow_null=True)
    map = AnalysisReportMapConfigurationSerializer(required=False, allow_null=True)
    timeline_chart = AnalysisReportTimelineChartConfigurationSerializer(required=False, allow_null=True)


class AnalysisReportContainerDataSerializer(TempClientIdMixin, serializers.ModelSerializer):
    id = IntegerIDField(required=False)

    class Meta:
        model = AnalysisReportContainerData
        fields = (
            'id',
            'client_id',
            'upload',
            'data',
        )

    def validate_upload(self, upload):
        report = self.context.get('report')
        if report is None:
            raise serializers.ValidationError(
                'Report needs to be created before assigning uploads to container'
            )
        if report.id != upload.report_id:
            raise serializers.ValidationError(
                'Upload within report are only allowed'
            )
        return upload


class AnalysisReportContainerSerializer(TempClientIdMixin, UserResourceSerializer):
    id = IntegerIDField(required=False)

    class Meta:
        model = AnalysisReportContainer
        fields = (
            'id',
            'client_id',
            'row',
            'column',
            'width',
            'height',
            'content_type',
            # Custom
            'style',
            'content_configuration',
            'content_data',
        )

    style = AnalysisReportContainerStyleSerializer(required=False, allow_null=True)

    # Content metadata
    content_configuration = AnalysisReportContainerContentConfigurationSerializer(
        required=False, allow_null=True)

    content_data = AnalysisReportContainerDataSerializer(many=True, source='analysisreportcontainerdata_set')

    # NOTE: This is a custom function (apps/user_resource/serializers.py::UserResourceSerializer)
    # This makes sure only scoped (individual Analysis Report) instances (container data) are updated.
    def _get_prefetch_related_instances_qs(self, qs):
        if self.instance:
            return qs.filter(container=self.instance)
        return qs.none()  # On create throw error if existing id is provided


class AnalysisReportSerializer(ProjectPropertySerializerMixin, UserResourceSerializer):
    class Meta:
        model = AnalysisReport
        fields = (
            'analysis',
            'slug',
            'title',
            'sub_title',
            'is_public',
            'organizations',
            # Custom
            'configuration',
            'containers',
        )

    configuration = AnalysisReportConfigurationSerializer(required=False, allow_null=True)
    containers = AnalysisReportContainerSerializer(many=True, source='analysisreportcontainer_set')

    # NOTE: This is a custom function (apps/user_resource/serializers.py::UserResourceSerializer)
    # This makes sure only scoped (individual Analysis Report) instances (containers) are updated.
    def _get_prefetch_related_instances_qs(self, qs):
        if self.instance:
            return qs.filter(report=self.instance)
        return qs.none()  # On create throw error if existing id is provided

    def validate_analysis(self, analysis):
        existing_analysis_id = self.instance and self.instance.analysis_id
        # NOTE: if changed, make sure user have access to that analysis
        if (
            analysis.id != existing_analysis_id and
            analysis.project_id != self.project.id
        ):
            raise serializers.ValidationError('You need access to analysis')
        return analysis


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
                extra={'data': {'errors': errors}},
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
    client_id = serializers.CharField(required=False)
    variables = AnalysisReportVariableSerializer(many=True)


class AnalysisReportUploadMetadataXlsxSerializer(serializers.Serializer):
    sheets = AnalysisReportUploadMetadataXlsxSheetSerializer(many=True)


class AnalysisReportUploadMetadataCsvSerializer(serializers.Serializer):
    header_row = serializers.IntegerField(required=False)
    variables = AnalysisReportVariableSerializer(many=True)


class AnalysisReportUploadMetadataGeoJsonSerializer(serializers.Serializer):
    variables = AnalysisReportVariableSerializer(many=True)


class AnalysisReportUploadMetadataSerializer(serializers.Serializer):
    xlsx = AnalysisReportUploadMetadataXlsxSerializer(required=False, allow_null=True)
    csv = AnalysisReportUploadMetadataCsvSerializer(required=False, allow_null=True)
    geojson = AnalysisReportUploadMetadataGeoJsonSerializer(required=False, allow_null=True)


class AnalysisReportUploadSerializer(ProjectPropertySerializerMixin, serializers.ModelSerializer):
    class Meta:
        model = AnalysisReportUpload
        fields = (
            'id',
            'report',
            'file',
            'type',
            # Custom
            'metadata',
        )

    metadata = AnalysisReportUploadMetadataSerializer()

    def validate_file(self, file):
        existing_file_id = self.instance and self.instance.file_id
        # NOTE: if changed, make sure only owner can assign files
        if (
            file.id != existing_file_id and
            file.created_by != self.context['request'].user
        ):
            raise serializers.ValidationError('Only owner can assign file')
        return file

    def validate_report(self, report):
        existing_report_id = self.instance and self.instance.report_id
        # NOTE: if changed, make sure user have access to that report
        if (
            report.id != existing_report_id and
            report.analysis.project_id != self.project.id
        ):
            raise serializers.ValidationError('You need access to report')
        return report
