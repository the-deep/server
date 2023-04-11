from typing import Callable
from django.conf import settings
from django.shortcuts import get_object_or_404

from rest_framework import serializers
from drf_dynamic_fields import DynamicFieldsMixin
from drf_writable_nested import UniqueFieldsMixin, NestedCreateMixin
from django.db import transaction

from utils.graphene.fields import generate_serializer_field_class
from deep.writable_nested_serializers import NestedUpdateMixin as CustomNestedUpdateMixin
from deep.serializers import (
    RemoveNullFieldsMixin,
    TempClientIdMixin,
    IntegerIDField,
    IdListField,
    GraphqlSupportDrfSerializerJSONField,
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
)
from .tasks import (
    trigger_topic_model,
    trigger_automatic_summary,
    trigger_automatic_ngram,
)


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
