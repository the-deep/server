from django.db import models
from django.conf import settings
from django.shortcuts import get_object_or_404

from rest_framework import serializers
from drf_dynamic_fields import DynamicFieldsMixin

from user_resource.serializers import UserResourceSerializer

from entry.serializers import SimpleEntrySerializer
from lead.models import Lead
from entry.models import Entry
from deep.serializers import (
    RemoveNullFieldsMixin,
    NestedCreateMixin,
    NestedUpdateMixin
)
from .models import (
    Analysis,
    AnalysisPillar,
    AnalyticalStatement,
    AnalyticalStatementEntry,
    DiscardedEntry
)


class AnlyticalEntriesSerializer(UserResourceSerializer):
    class Meta:
        model = AnalyticalStatementEntry
        fields = ('id', 'client_id', 'order', 'entry')
        read_only_fields = ('analytical_statement',)


class AnalyticalStatementSerializer(
    RemoveNullFieldsMixin,
    DynamicFieldsMixin,
    UserResourceSerializer,
    NestedCreateMixin,
    NestedUpdateMixin,
):
    analytical_entries = AnlyticalEntriesSerializer(source='analyticalstatemententry_set', many=True, required=False)

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
        if data['entry'].project != analysis_pillar.analysis.project:
            raise serializers.ValidationError(
                f'Analysis pillar project doesnot match Entry project'
            )
        return data


class AnalysisPillarSerializer(
    RemoveNullFieldsMixin,
    DynamicFieldsMixin,
    UserResourceSerializer,
    NestedCreateMixin,
    NestedUpdateMixin,
):
    assignee_name = serializers.CharField(source='assignee.username', read_only=True)
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
                f'Analytical statement count must be less than{settings.ANALYTICAL_STATEMENT_COUNT}'
            )
        return data


class AnalysisSerializer(
    RemoveNullFieldsMixin,
    DynamicFieldsMixin,
    UserResourceSerializer,
    NestedCreateMixin,
    NestedUpdateMixin,
):
    analysis_pillar = AnalysisPillarSerializer(many=True, source='analysispillar_set', required=False)
    team_lead_name = serializers.CharField(source='team_lead.username', read_only=True)

    class Meta:
        model = Analysis
        fields = '__all__'
        read_only_fields = ('project',)

    def validate(self, data):
        data['project_id'] = int(self.context['view'].kwargs['project_id'])
        return data


class AnalysisSummarySerializer(serializers.ModelSerializer):
    team_lead_name = serializers.CharField()
    pillar_list = serializers.SerializerMethodField()
    framework_overview = serializers.SerializerMethodField()
    publication_date = serializers.SerializerMethodField()
    pillar_summary = serializers.SerializerMethodField()
    total_entries = serializers.IntegerField()
    total_sources = serializers.IntegerField()
    analyzed_entries = serializers.IntegerField()
    analyzed_sources = serializers.IntegerField()

    class Meta:
        model = Analysis
        fields = ('id', 'team_lead', 'team_lead_name', 'pillar_list', 'framework_overview', 'publication_date',
                  'analyzed_entries', 'analyzed_sources', 'total_entries', 'total_sources', 'pillar_summary')

    def get_pillar_list(self, analysis):
        return list(
            AnalysisPillar.objects.filter(
                analysis=analysis
            ).values('id', 'title', assignee_username=models.F('assignee__username'))
        )

    def get_framework_overview(self, analysis):
        return list(
            AnalysisPillar.objects.filter(
                analysis=analysis
            ).annotate(
                entries_dragged=models.functions.Coalesce(models.Subquery(
                    AnalyticalStatement.objects.filter(
                        analysis_pillar=models.OuterRef('pk')
                    ).order_by().values('analysis_pillar').annotate(count=models.Count('entries', distinct=True))
                    .values('count')[:1],
                    output_field=models.IntegerField(),
                ), 0),
                entries_discarded=models.functions.Coalesce(models.Subquery(
                    DiscardedEntry.objects.filter(
                        analysis_pillar=models.OuterRef('pk')
                    ).order_by().values('analysis_pillar').annotate(count=models.Count('entry', distinct=True))
                    .values('count')[:1],
                    output_field=models.IntegerField(),
                ), 0)
            ).values('id', 'title', entries_analyzed=models.F('entries_dragged') + models.F('entries_discarded'))
        )

    def get_publication_date(self, analysis):
        lead_qs = Lead.objects.filter(
            project=analysis.project
        ).annotate(
            entries_count=models.functions.Coalesce(models.Subquery(
                AnalyticalStatementEntry.objects.filter(
                    entry__lead_id=models.OuterRef('pk')
                ).order_by().values('entry__lead_id').annotate(count=models.Count('*'))
                .values('count')[:1],
                output_field=models.IntegerField(),
            ), 0)
        ).filter(entries_count__gt=0).order_by('created_at')
        lead_first_created_date = lead_qs.values_list('created_at__date', flat=True).first()
        lead_last_created_date = lead_qs.values_list('created_at__date', flat=True).last()
        return {
            'start_date': lead_first_created_date,
            'end_date': lead_last_created_date
        }

    def get_pillar_summary(self, analysis):
        pillar_list = AnalysisPillar.objects.filter(
            analysis=analysis
        ).annotate(
           dragged_entries=models.functions.Coalesce(
                models.Subquery(
                    AnalyticalStatement.objects.filter(
                        analysis_pillar=models.OuterRef('pk')
                    ).order_by().values('analysis_pillar').annotate(count=models.Count('entries', distinct=True))
                    .values('count')[:1],
                    output_field=models.IntegerField(),
                ), 0),
            discarded_entries=models.functions.Coalesce(
                models.Subquery(
                    DiscardedEntry.objects.filter(
                        analysis_pillar=models.OuterRef('pk')
                    ).order_by().values('analysis_pillar__analysis').annotate(count=models.Count('entry', distinct=True))
                    .values('count')[:1],
                    output_field=models.IntegerField(),
                ), 0),
        ).annotate(
            entries_analyzed=models.F('dragged_entries') + models.F('discarded_entries')
        )
        return [
                {
                    'id': pillar.id,
                    'pillar_title': pillar.title,
                    'assignee': pillar.assignee.username,
                    'analytical_statements': AnalyticalStatement.objects.filter(
                        analysis_pillar=pillar
                    ).annotate(
                        entries_count=models.Count('entries', distinct=True)).values(
                        'entries_count', 'id', 'statement'
                    ),
                    'created_at': pillar.created_at,
                    'analytical_statement_count': AnalyticalStatement.objects.filter(analysis_pillar=pillar).count(),
                    'entries_analyzed': pillar.entries_analyzed
                } for pillar in pillar_list
            ]
