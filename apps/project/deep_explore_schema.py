import graphene

from graphene_django import DjangoObjectType
from django.db import models
from django.db.models.functions import (
    TruncMonth,
    TruncDay,
    Coalesce,
    Cast,
)
from django.contrib.postgres.aggregates.general import ArrayAgg, StringAgg
from django.contrib.postgres.fields.jsonb import KeyTextTransform

from deep.serializers import URLCachedFileField
# Schema
from organization.schema import OrganizationType
# Models
from organization.models import Organization
from geo.models import Region
from user.models import User
from project.models import Project, ProjectMembership
from lead.models import Lead
from entry.models import Entry
from analysis_framework.models import AnalysisFramework

# Filters
from project.filter_set import ExploreProjectFilterDataInputType, ExploreProjectFilterSet


class ExploreDeepFilter(graphene.InputObjectType):
    date_from = graphene.Date(required=True)
    date_to = graphene.Date(required=True)
    project = ExploreProjectFilterDataInputType()


class ExploreStastOrganizationType(OrganizationType):
    class Meta:
        model = Organization
        skip_registry = True
        fields = (
            'id',
            'title',
            'short_name',
            'long_name',
            'url',
            'logo',
            'organization_type',
            'verified',
        )
    source_count = graphene.Int()
    project_count = graphene.Int()


class ExploreDashboardProjectRegion(DjangoObjectType):
    class Meta:
        model = Region
        skip_registry = True
        only_fields = (
            'id', 'centroid',
        )
    project_ids = graphene.List(graphene.NonNull(graphene.ID))


class ExploreDashboardProjectType(DjangoObjectType):
    class Meta:
        model = Project
        skip_registry = True
        fields = (
            'id',
            'title',
            'description',
            'created_at',
        )

    analysis_framework = graphene.ID(source='analysis_framework_id')
    analysis_framework_title = graphene.String()
    regions_title = graphene.String()
    organizations_title = graphene.String()
    number_of_users = graphene.Int(required=True)
    number_of_leads = graphene.Int(required=True)
    number_of_entries = graphene.Int(required=True)
    analysis_framework_preview_image = graphene.String()

    @staticmethod
    def resolve_analysis_framework_preview_image(root, info, **kwargs):
        if root.preview_image:
            return info.context.request.build_absolute_uri(
                URLCachedFileField.name_to_representation(root.preview_image)
            )
        return None


class ExploreDashboardStatType(graphene.ObjectType):
    total_projects = graphene.Int()
    total_registered_users = graphene.Int()
    total_leads = graphene.Int()
    total_entries = graphene.Int()
    total_active_users = graphene.Int()
    total_authors = graphene.Int()
    total_publishers = graphene.Int()

    top_ten_authors = graphene.List(graphene.NonNull(ExploreStastOrganizationType))
    top_ten_publishers = graphene.List(graphene.NonNull(ExploreStastOrganizationType))
    top_ten_frameworks = graphene.List(
        graphene.NonNull(
            type('ExploreDeepStatTopActiveFrameworksType', (graphene.ObjectType,), {
                'analysis_framework_id': graphene.Field(graphene.NonNull(graphene.ID)),
                'analysis_framework_title': graphene.String(),
                'project_count': graphene.NonNull(graphene.Int),
                'entry_count': graphene.NonNull(graphene.Int)
            })
        )
    )
    top_ten_project_users = graphene.List(
        graphene.NonNull(
            type('ExploreDeepStatTopProjectType', (graphene.ObjectType,), {
                'project_id': graphene.Field(graphene.NonNull(graphene.ID)),
                'project_title': graphene.String(),
                'user_count': graphene.NonNull(graphene.Int),
            })
        )
    )
    top_ten_project_entries = graphene.List(
        graphene.NonNull(
            type('ExploreDeepStatTopProjectEntryType', (graphene.ObjectType,), {
                'project_id': graphene.Field(graphene.NonNull(graphene.ID)),
                'project_title': graphene.String(),
                'source_count': graphene.NonNull(graphene.Int),
                'entry_count': graphene.NonNull(graphene.Int),
            })
        )
    )
    project_by_region = graphene.List(ExploreDashboardProjectRegion)
    project_aggregation_monthly = graphene.List(
        graphene.NonNull(
            type('ExploreDeepStatProjetAggregationMonthly', (graphene.ObjectType,), {
                'date': graphene.Date(required=True),
                'project_count': graphene.String(required=True),
            })
        )
    )
    project_aggregation_daily = graphene.List(
        graphene.NonNull(
            type('ExploreDeepStatProjetAggregationDaily', (graphene.ObjectType,), {
                'date': graphene.Date(required=True),
                'project_count': graphene.String(required=True),
            })
        )
    )
    projects = graphene.List(ExploreDashboardProjectType)

    @staticmethod
    def custom_resolver(info, filter):
        # TODO: Don't calculate if not needed
        if filter:
            date_from = filter.get('date_from')
            date_to = filter.get('date_to')

            # project specific filter
            project_qs = Project.objects.filter(
                created_at__gte=date_from,
                created_at__lte=date_to,
            ).exclude(is_test=True)
            project_filter = filter.get('project')
            if project_filter:
                project_qs = ExploreProjectFilterSet(
                    request=info.context.request,
                    queryset=project_qs,
                    data=project_filter
                ).qs

            total_projects = project_qs.distinct().count()
            total_registered_users = User.objects.filter(
                is_active=True,
            ).count()

            lead_qs = Lead.objects.filter(
                created_at__gte=date_from,
                created_at__lte=date_to,
                project__in=project_qs
            )
            total_leads = lead_qs.distinct().count()

            entry_qs = Entry.objects.filter(
                created_at__gte=date_from,
                created_at__lte=date_to,
                project__in=project_qs
            )
            total_entries = entry_qs.distinct().count()
            total_authors = lead_qs.values('authors').distinct().count()
            total_publishers = lead_qs.values('source').distinct().count()
            total_active_users = lead_qs.values('created_by').union(
                entry_qs.values('created_by')).count()

            organization_qs = Organization.objects.filter(
                created_at__gte=date_from,
                created_at__lte=date_to
            )
            top_ten_authors = organization_qs.annotate(
                source_count=models.functions.Coalesce(models.Subquery(
                    Lead.objects.filter(
                        authors=models.OuterRef('pk')
                    ).order_by().values('authors')
                    .annotate(cnt=models.Count('*')).values('cnt')[:1],
                    output_field=models.IntegerField(),
                ), 0),
                project_count=models.functions.Coalesce(models.Subquery(
                    Lead.objects.filter(
                        authors=models.OuterRef('pk')
                    ).order_by().values('authors')
                    .annotate(cnt=models.Count('project_id', distinct=True)).values('cnt')[:1],
                    output_field=models.IntegerField(),
                ), 0),
            ).order_by('-source_count', '-project_count')[:10]

            top_ten_publishers = organization_qs.annotate(
                source_count=models.functions.Coalesce(models.Subquery(
                    Lead.objects.filter(
                        source=models.OuterRef('pk')
                    ).order_by().values('source')
                    .annotate(cnt=models.Count('*')).values('cnt')[:1],
                    output_field=models.IntegerField(),
                ), 0),
                project_count=models.functions.Coalesce(models.Subquery(
                    Lead.objects.filter(
                        source=models.OuterRef('pk')
                    ).order_by().values('source')
                    .annotate(cnt=models.Count('project_id', distinct=True)).values('cnt')[:1],
                    output_field=models.IntegerField(),
                ), 0),
            ).order_by('-source_count', '-project_count')[:10]

            analysis_framework_qs = AnalysisFramework.objects.filter(
                created_at__gte=date_from,
                created_at__lte=date_to,
            )
            top_ten_frameworks = analysis_framework_qs.distinct().annotate(
                project_count=models.functions.Coalesce(
                    models.Subquery(
                        Project.objects.filter(
                            analysis_framework=models.OuterRef('pk')
                        ).order_by().values('analysis_framework').annotate(
                            count=models.Count('id', distinct=True),
                        ).values('count')[:1],
                        output_field=models.IntegerField()
                    ), 0),
                entry_count=models.functions.Coalesce(
                    models.Subquery(
                        Entry.objects.filter(
                            project__analysis_framework=models.OuterRef('pk')
                        ).order_by().values('project__analysis_framework').annotate(
                            count=models.Count('id', distinct=True)
                        ).values('count')[:1],
                        output_field=models.IntegerField()
                    ), 0),
            ).order_by('-project_count', '-entry_count').values(
                analysis_framework_id=models.F('id'),
                analysis_framework_title=models.F('title'),
                project_count=models.F('project_count'),
                entry_count=models.F('entry_count'),
            )[:10]

            top_ten_project_users = project_qs.distinct().annotate(
                user_count=models.functions.Coalesce(
                    models.Subquery(
                        ProjectMembership.objects.filter(
                            project=models.OuterRef('pk')
                        ).order_by().values('project').annotate(
                            count=models.Count('member', distinct=True),
                        ).values('count')[:1],
                        output_field=models.IntegerField()
                    ), 0),
            ).order_by('-user_count').values(
                project_id=models.F('id'),
                project_title=models.F('title'),
                user_count=models.F('user_count'),
            )[:10]

            top_ten_project_entries = project_qs.distinct().annotate(
                source_count=models.functions.Coalesce(
                    models.Subquery(
                        Lead.objects.filter(
                            project=models.OuterRef('pk')
                        ).order_by().values('project').annotate(
                            count=models.Count('id', distinct=True),
                        ).values('count')[:1],
                        output_field=models.IntegerField()
                    ), 0),
                entry_count=models.functions.Coalesce(
                    models.Subquery(
                        Entry.objects.filter(
                            project=models.OuterRef('pk')
                        ).order_by().values('project').annotate(
                            count=models.Count('id', distinct=True),
                        ).values('count')[:1],
                        output_field=models.IntegerField()
                    ), 0),
            ).order_by('-source_count', '-entry_count').values(
                project_id=models.F('id'),
                project_title=models.F('title'),
                source_count=models.F('source_count'),
                entry_count=models.F('entry_count')
            )[:10]

            project_by_region = Region.objects.annotate(
                project_ids=ArrayAgg(
                    'project',
                    distinct=True,
                    ordering='project',
                    filter=models.Q(project__in=project_qs),
                ),
            ).filter(project_ids__isnull=False).only('id', 'centroid')

            project_aggregation_monthly = project_qs.values(
                date=TruncMonth('created_at')
            ).annotate(
                project_count=models.Count('id')
            ).order_by('date')

            project_aggregation_daily = project_qs.values(
                date=TruncDay('created_at')
            ).annotate(
                project_count=models.Count('id')
            ).order_by('date')

            projects = project_qs.annotate(
                analysis_framework_title=models.Case(
                    models.When(
                        analysis_framework__is_private=False,
                        then=models.F('analysis_framework__title')
                    ),
                    default=None,
                ),
                preview_image=models.Case(
                    models.When(
                        analysis_framework__is_private=False,
                        then=models.F('analysis_framework__preview_image')
                    ),
                    default=None
                ),
                regions_title=StringAgg(
                    'regions__title',
                    ', ',
                    filter=models.Q(
                        ~models.Q(regions__title=''),
                        regions__public=True,
                        regions__title__isnull=False,
                    ),
                    distinct=True,
                ),
                organizations_title=StringAgg(
                    models.Case(
                        models.When(
                            projectorganization__organization__parent__isnull=False,
                            then='projectorganization__organization__parent__title'
                        ),
                        default='projectorganization__organization__title',
                    ),
                    ', ',
                    distinct=True,
                ),
                **{
                    key: Coalesce(
                        Cast(KeyTextTransform(key, 'stats_cache'), models.IntegerField()),
                        0,
                    )
                    for key in ['number_of_leads', 'number_of_users', 'number_of_entries']
                },
            ).only(
                'id',
                'title',
                'description',
                'analysis_framework_id',
                'created_at',
            ).distinct()

            return dict(
                total_projects=total_projects,
                total_registered_users=total_registered_users,
                total_leads=total_leads,
                total_entries=total_entries,
                total_authors=total_authors,
                total_publishers=total_publishers,
                total_active_users=total_active_users,
                top_ten_authors=top_ten_authors,
                top_ten_frameworks=top_ten_frameworks,
                top_ten_project_users=top_ten_project_users,
                top_ten_project_entries=top_ten_project_entries,
                project_by_region=project_by_region,
                project_aggregation_monthly=project_aggregation_monthly,
                project_aggregation_daily=project_aggregation_daily,
                top_ten_publishers=top_ten_publishers,
                projects=projects,
            )
