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
from utils.graphene.geo_scalars import PointScalar
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
from deep_explore.models import EntriesCountByGeoAreaAggregate

# Filters
from project.filter_set import ExploreProjectFilterDataInputType, ExploreProjectFilterSet


class ExploreCountByDateType(graphene.ObjectType):
    date = graphene.Date(required=True)
    count = graphene.Int(required=True)


ExploreCountByDateListType = graphene.List(graphene.NonNull(ExploreCountByDateType))


def count_by_type_generator(type_name):
    return graphene.List(
        graphene.NonNull(
            type(type_name, (graphene.ObjectType,), {
                'date': graphene.Date(required=True),
                'count': graphene.Int(required=True),
            })
        )
    )


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
    leads_count = graphene.Int()
    projects_count = graphene.Int()


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
                'projects_count': graphene.NonNull(graphene.Int),
                'entries_count': graphene.NonNull(graphene.Int)
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
                'leads_count': graphene.NonNull(graphene.Int),
                'entries_count': graphene.NonNull(graphene.Int),
            })
        )
    )

    leads_count_by_month = graphene.Field(ExploreCountByDateListType)
    leads_count_by_day = graphene.Field(ExploreCountByDateListType)

    entries_count_by_month = graphene.Field(ExploreCountByDateListType)
    entries_count_by_day = graphene.Field(ExploreCountByDateListType)
    entries_count_by_region = graphene.List(
        graphene.NonNull(
            type('ExploreDeepStatEntriesCountByCentroidType', (graphene.ObjectType,), {
                'centroid': PointScalar(),
                'date': graphene.Date(required=True),
                'count': graphene.NonNull(graphene.Int),
            })
        )
    )

    projects_by_region = graphene.List(ExploreDashboardProjectRegion)
    projects_count_by_month = graphene.Field(ExploreCountByDateListType)
    projects_count_by_day = graphene.Field(ExploreCountByDateListType)

    projects = graphene.List(ExploreDashboardProjectType)

    @staticmethod
    def custom_resolver(info, filter):
        def _count_by_date(qs, trunc_func):
            # Used by ExploreCountByDateListType
            return qs.values(
                date=trunc_func('created_at')
            ).annotate(
                count=models.Count('id')
            ).order_by('date')

        # TODO: Don't calculate if not needed
        if filter:
            # Use django filter here with timezone support
            date_from = filter.get('date_from')
            date_to = filter.get('date_to')

            # project specific filter
            projects_qs = Project.objects.filter(
                created_at__gte=date_from,
                created_at__lte=date_to,
            ).exclude(is_test=True)
            project_filter = filter.get('project')
            if project_filter:
                projects_qs = ExploreProjectFilterSet(
                    request=info.context.request,
                    queryset=projects_qs,
                    data=project_filter
                ).qs

            total_projects = projects_qs.distinct().count()
            total_registered_users = User.objects.filter(
                is_active=True,
            ).count()

            leads_qs = Lead.objects.filter(
                created_at__gte=date_from,
                created_at__lte=date_to,
                project__in=projects_qs
            )
            total_leads = leads_qs.distinct().count()

            entries_qs = Entry.objects.filter(
                created_at__gte=date_from,
                created_at__lte=date_to,
                project__in=projects_qs
            )
            total_entries = entries_qs.distinct().count()
            total_authors = leads_qs.values('authors').distinct().count()
            total_publishers = leads_qs.values('source').distinct().count()
            total_active_users = leads_qs.values('created_by').union(
                entries_qs.values('created_by')
            ).count()

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
                projects_count=models.functions.Coalesce(models.Subquery(
                    Lead.objects.filter(
                        authors=models.OuterRef('pk')
                    ).order_by().values('authors')
                    .annotate(cnt=models.Count('project_id', distinct=True)).values('cnt')[:1],
                    output_field=models.IntegerField(),
                ), 0),
            ).order_by('-source_count', '-projects_count')[:10]

            top_ten_publishers = organization_qs.annotate(
                source_count=models.functions.Coalesce(models.Subquery(
                    Lead.objects.filter(
                        source=models.OuterRef('pk')
                    ).order_by().values('source')
                    .annotate(cnt=models.Count('*')).values('cnt')[:1],
                    output_field=models.IntegerField(),
                ), 0),
                projects_count=models.functions.Coalesce(models.Subquery(
                    Lead.objects.filter(
                        source=models.OuterRef('pk')
                    ).order_by().values('source')
                    .annotate(cnt=models.Count('project_id', distinct=True)).values('cnt')[:1],
                    output_field=models.IntegerField(),
                ), 0),
            ).order_by('-source_count', '-projects_count')[:10]

            analysis_framework_qs = AnalysisFramework.objects.filter(
                created_at__gte=date_from,
                created_at__lte=date_to,
            )
            top_ten_frameworks = analysis_framework_qs.distinct().annotate(
                projects_count=models.functions.Coalesce(
                    models.Subquery(
                        Project.objects.filter(
                            analysis_framework=models.OuterRef('pk')
                        ).order_by().values('analysis_framework').annotate(
                            count=models.Count('id', distinct=True),
                        ).values('count')[:1],
                        output_field=models.IntegerField()
                    ), 0),
                entries_count=models.functions.Coalesce(
                    models.Subquery(
                        Entry.objects.filter(
                            project__analysis_framework=models.OuterRef('pk')
                        ).order_by().values('project__analysis_framework').annotate(
                            count=models.Count('id', distinct=True)
                        ).values('count')[:1],
                        output_field=models.IntegerField()
                    ), 0),
            ).order_by('-projects_count', '-entries_count').values(
                'projects_count',
                'entries_count',
                analysis_framework_id=models.F('id'),
                analysis_framework_title=models.F('title'),
            )[:10]

            top_ten_project_users = projects_qs.distinct().annotate(
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

            top_ten_project_entries = projects_qs.distinct().annotate(
                leads_count=models.functions.Coalesce(
                    models.Subquery(
                        Lead.objects.filter(
                            project=models.OuterRef('pk')
                        ).order_by().values('project').annotate(
                            count=models.Count('id', distinct=True),
                        ).values('count')[:1],
                        output_field=models.IntegerField()
                    ), 0),
                entries_count=models.functions.Coalesce(
                    models.Subquery(
                        Entry.objects.filter(
                            project=models.OuterRef('pk')
                        ).order_by().values('project').annotate(
                            count=models.Count('id', distinct=True),
                        ).values('count')[:1],
                        output_field=models.IntegerField()
                    ), 0),
            ).order_by('-leads_count', '-entries_count').values(
                'leads_count',
                'entries_count',
                project_id=models.F('id'),
                project_title=models.F('title'),
            )[:10]

            projects_by_region = Region.objects.annotate(
                project_ids=ArrayAgg(
                    'project',
                    distinct=True,
                    ordering='project',
                    filter=models.Q(project__in=projects_qs),
                ),
            ).filter(project_ids__isnull=False).only('id', 'centroid')

            # ---- By month/day
            entries_count_by_month = _count_by_date(entries_qs, TruncMonth)
            entries_count_by_day = _count_by_date(entries_qs, TruncDay)
            entries_count_by_region = EntriesCountByGeoAreaAggregate.objects\
                .filter(
                    date__gte=date_from,
                    date__lte=date_to,
                    project__in=projects_qs,
                    geo_area__centroid__isempty=False,
                ).annotate(
                    date__month=TruncMonth('date')
                ).order_by('date__month').values('date__month', 'geo_area').annotate(
                    count=models.Sum('entries_count'),
                ).values(
                    'count',
                    date=models.F('date__month'),
                    centroid=models.F('geo_area__centroid'),
                )

            leads_count_by_month = _count_by_date(leads_qs, TruncMonth)
            leads_count_by_day = _count_by_date(leads_qs, TruncDay)

            projects_count_by_month = _count_by_date(projects_qs, TruncMonth)
            projects_count_by_day = _count_by_date(projects_qs, TruncDay)

            projects = projects_qs.annotate(
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
                # Single metrics
                total_projects=total_projects,
                total_registered_users=total_registered_users,
                total_leads=total_leads,
                total_entries=total_entries,
                total_authors=total_authors,
                total_publishers=total_publishers,
                total_active_users=total_active_users,
                # Leads by (TODO: Fetch when needed)
                leads_count_by_month=leads_count_by_month,
                leads_count_by_day=leads_count_by_day,
                # Projects by (TODO: Fetch when needed)
                projects_by_region=projects_by_region,
                projects_count_by_month=projects_count_by_month,
                projects_count_by_day=projects_count_by_day,
                # Entries by
                entries_count_by_month=entries_count_by_month,
                entries_count_by_day=entries_count_by_day,
                entries_count_by_region=entries_count_by_region,
                # Top ten aggregates
                top_ten_authors=top_ten_authors,
                top_ten_frameworks=top_ten_frameworks,
                top_ten_project_users=top_ten_project_users,
                top_ten_project_entries=top_ten_project_entries,
                top_ten_publishers=top_ten_publishers,
                # Projects (TODO: Pagination)
                projects=projects,
            )
