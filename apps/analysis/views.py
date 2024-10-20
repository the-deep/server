from django.shortcuts import get_object_or_404

from rest_framework.decorators import action
from rest_framework import (
    permissions,
    views,
    response,
    viewsets,
    status
)

from deep.permissions import IsProjectMember, ModifyPermission
from entry.views import EntryFilterView

from .models import (
    Analysis,
    AnalysisPillar,
    AnalyticalStatement,
    DiscardedEntry,
)
from .serializers import (
    AnalysisSerializer,
    AnalysisPillarSerializer,
    AnalyticalStatementSerializer,
    AnalysisSummarySerializer,
    AnalysisPillarSummarySerializer,
    DiscardedEntrySerializer,
    AnalysisCloneInputSerializer
)
from .filter_set import (
    AnalysisFilterSet,
    DiscardedEntryFilterSet,
)


class AnalysisViewSet(viewsets.ModelViewSet):
    serializer_class = AnalysisSerializer
    permission_classes = [permissions.IsAuthenticated, IsProjectMember, ModifyPermission]
    filterset_class = AnalysisFilterSet

    def get_queryset(self):
        return Analysis.objects.filter(project=self.kwargs['project_id']).select_related(
            'project',
            'team_lead',
        )

    @action(
        detail=False,
        url_path='summary'
    )
    def get_summary(self, request, project_id, pk=None, version=None):
        queryset = self.filter_queryset(self.get_queryset())
        queryset = Analysis.annotate_for_analysis_summary(project_id, queryset, self.request.user)
        page = self.paginate_queryset(queryset)
        # NOTE: Calculating here and passing as context since we can't calculate union in subquery in Django for now
        context = {
            'analyzed_sources': Analysis.get_analyzed_sources(page),
            'analyzed_entries': Analysis.get_analyzed_entries(page)
        }
        serializer = AnalysisSummarySerializer(page, many=True, context=context, partial=True)
        return self.get_paginated_response(serializer.data)

    @action(
        detail=True,
        url_path='clone',
        methods=['post']
    )
    def clone_analysis(self, request, project_id, pk=None, version=None):
        analysis = self.get_object()
        input_serializer = AnalysisCloneInputSerializer(data=request.data)
        if input_serializer.is_valid():
            title = input_serializer.validated_data['title']
            end_date = input_serializer.validated_data['end_date']
            new_analysis = analysis.clone_analysis(title, end_date)
            serializer = AnalysisSerializer(
                new_analysis,
                context={'request': request},
            )
            return response.Response(
                serializer.data,
                status=status.HTTP_201_CREATED,
            )
        else:
            return response.Response(
                input_serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )


class AnalysisPillarViewSet(viewsets.ModelViewSet):
    serializer_class = AnalysisPillarSerializer
    permission_classes = [permissions.IsAuthenticated, IsProjectMember, ModifyPermission]

    def get_queryset(self):
        return AnalysisPillar.objects\
            .filter(
                analysis=self.kwargs['analysis_id'],
                analysis__project=self.kwargs['project_id'],
            ).select_related('analysis', 'assignee', 'assignee__profile')

    @action(
        detail=False,
        url_path='summary',
    )
    def get_summary(self, request, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        queryset = AnalysisPillar.annotate_for_analysis_pillar_summary(queryset)
        page = self.paginate_queryset(queryset)
        serializer = AnalysisPillarSummarySerializer(page, many=True, partial=True)
        return self.get_paginated_response(serializer.data)


class AnalysisPillarDiscardedEntryViewSet(viewsets.ModelViewSet):
    serializer_class = DiscardedEntrySerializer
    permission_classes = [permissions.IsAuthenticated, IsProjectMember, ModifyPermission]
    filterset_class = DiscardedEntryFilterSet

    def get_queryset(self):
        return DiscardedEntry.objects.filter(analysis_pillar=self.kwargs['analysis_pillar_id'])

    def get_serializer_context(self):
        return {
            **super().get_serializer_context(),
            'analysis_pillar_id': self.kwargs.get('analysis_pillar_id'),
        }


class AnalysisPillarEntryViewSet(EntryFilterView):
    permission_classes = [permissions.IsAuthenticated, IsProjectMember, ModifyPermission]

    def get_queryset(self):
        queryset = super().get_queryset()
        filters = self.get_entries_filters()
        analysis_pillar_id = self.kwargs['analysis_pillar_id']
        analysis_pillar = get_object_or_404(AnalysisPillar, id=self.kwargs['analysis_pillar_id'])
        # filtering out the entries whose lead published_on date is less than analysis end_date
        queryset = queryset.filter(
            project=analysis_pillar.analysis.project,
            lead__published_on__lte=analysis_pillar.analysis.end_date
        )
        discarded_entries_qs = DiscardedEntry.objects.filter(analysis_pillar=analysis_pillar_id).values('entry')
        if filters.get('discarded'):
            return queryset.filter(id__in=discarded_entries_qs)
        queryset = queryset.exclude(id__in=discarded_entries_qs)
        exclude_entries = filters.get('exclude_entries')
        if exclude_entries:
            queryset = queryset.exclude(id__in=exclude_entries)
        return queryset


class AnalyticalStatementViewSet(viewsets.ModelViewSet):
    serializer_class = AnalyticalStatementSerializer
    permissions_classes = [permissions.IsAuthenticated, IsProjectMember, ModifyPermission]

    def get_queryset(self):
        return AnalyticalStatement.objects.filter(analysis_pillar=self.kwargs['analysis_pillar_id']).select_related(
            'analysis_pillar',
        ).prefetch_related(
            'entries',
            'analyticalstatemententry_set',
        )


class DiscardedEntryOptionsView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, version=None):
        options = [
            {
                'key': tag.value,
                'value': tag.label,
            } for tag in DiscardedEntry.TagType
        ]
        return response.Response(options)
