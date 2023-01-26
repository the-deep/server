import copy
import graphene
from datetime import timedelta
from dataclasses import dataclass

from django.db import models
from django.utils import timezone
from django.db.models.functions import (
    TruncMonth,
    TruncDay,
)
from django.contrib.postgres.aggregates.general import ArrayAgg
from graphene_django import DjangoObjectType, DjangoListField

from deep.caches import CacheKey, CacheHelper
from utils.graphene.geo_scalars import PointScalar
from utils.graphene.types import FileFieldType
from organization.models import Organization
from geo.models import Region
from user.models import User
from project.models import Project, ProjectMembership
from lead.models import Lead
from entry.models import Entry
from analysis_framework.models import AnalysisFramework
from deep_explore.models import EntriesCountByGeoAreaAggregate, PublicExploreYearSnapshot

from .filter_set import ExploreProjectFilterDataInputType, ExploreProjectFilterSet


# TODO?
NODE_CACHE_TIMEOUT = 60 * 60 * 1  # 1 Hour


def node_cache(cache_key):
    def cache_key_gen(root: ExploreDashboardStatRoot, *_):
        return root.cache_key

    return CacheHelper.gql_cache(
        cache_key,
        timeout=NODE_CACHE_TIMEOUT,
        cache_key_gen=cache_key_gen,
    )


def get_global_filters(_filter, date_field='created_at'):
    return {
        f'{date_field}__gte': _filter['date_from'],
        f'{date_field}__lte': _filter['date_to'],
    }


def project_queryset():
    return Project.objects.filter(is_private=False)


class ExploreCountByDateType(graphene.ObjectType):
    date = graphene.Date(required=True)
    count = graphene.Int(required=True)


ExploreCountByDateListType = graphene.List(graphene.NonNull(ExploreCountByDateType))


def count_by_date_queryset_generator(qs, trunc_func):
    # Used by ExploreCountByDateListType
    return qs.values(
        date=trunc_func('created_at')
    ).annotate(
        count=models.Count('id')
    ).order_by('date')


def get_top_ten_organizations_list(queryset, leads_qs, project_qs, lead_field):
    return [
        {
            **data,
            'id': data.pop('org_id'),
            'title': data.pop('org_title'),
        }
        for data in leads_qs.filter(
            **{f'{lead_field}__in': queryset},
        ).annotate(
            org_id=models.functions.Coalesce(
                models.F(f'{lead_field}__parent'),
                models.F(f'{lead_field}__id')
            ),
            org_title=models.functions.Coalesce(
                models.F(f'{lead_field}__parent__title'),
                models.F(f'{lead_field}__title')
            ),
        ).order_by().values('org_id', 'org_title').annotate(
            leads_count=models.Count('id', distinct=True),
            projects_count=models.Count(
                'project', distinct=True, filter=models.Q(project__in=project_qs)
            ),
        ).order_by('-leads_count', '-projects_count').values(
            'org_id',
            'org_title',
            'leads_count',
            'projects_count',
        ).distinct()[:10]
    ]


class ExploreDeepFilterInputType(graphene.InputObjectType):
    date_from = graphene.DateTime(required=True)
    date_to = graphene.DateTime(required=True)
    project = ExploreProjectFilterDataInputType()


class ExploreStastOrganizationType(graphene.ObjectType):
    id = graphene.ID(required=True)
    title = graphene.String(required=True)
    leads_count = graphene.Int()
    projects_count = graphene.Int()


class ExploreDashboardProjectRegion(graphene.ObjectType):
    id = graphene.ID(required=True)
    centroid = PointScalar()
    project_ids = graphene.List(graphene.NonNull(graphene.ID))


class ExploreDeepStatTopActiveFrameworksType(graphene.ObjectType):
    id = graphene.ID(required=True)
    title = graphene.String(required=True)
    projects_count = graphene.NonNull(graphene.Int)
    entries_count = graphene.NonNull(graphene.Int)


class ExploreDeepStatTopProjectType(graphene.ObjectType):
    id = graphene.ID(required=True)
    title = graphene.String()
    users_count = graphene.Int(required=True)


class ExploreDeepStatTopProjectEntryType(graphene.ObjectType):
    id = graphene.ID(required=True)
    title = graphene.String()
    leads_count = graphene.NonNull(graphene.Int)
    entries_count = graphene.NonNull(graphene.Int)


class ExploreDeepStatEntriesCountByCentroidType(graphene.ObjectType):
    centroid = PointScalar()
    count = graphene.NonNull(graphene.Int)


@dataclass
class ExploreDashboardStatRoot():
    cache_key: str
    analysis_framework_qs: models.QuerySet
    entries_count_by_geo_area_aggregate_qs: models.QuerySet
    entries_qs: models.QuerySet
    leads_qs: models.QuerySet
    organization_qs: models.QuerySet
    registered_users: models.QuerySet
    projects_qs: models.QuerySet
    ref_projects_qs: models.QuerySet  # Without global filters


# XXX: Make sure to update deep_explore.tasks.DEEP_EXPLORE_FULL_QUERY
class ExploreDashboardStatType(graphene.ObjectType):
    total_projects = graphene.Int(required=True)
    total_registered_users = graphene.Int(required=True)
    total_leads = graphene.Int(required=True)
    total_entries = graphene.Int(required=True)
    total_entries_added_last_week = graphene.Int(required=True)
    total_active_users = graphene.Int(required=True)
    total_authors = graphene.Int(required=True)
    total_publishers = graphene.Int(required=True)

    top_ten_authors = graphene.List(graphene.NonNull(ExploreStastOrganizationType))
    top_ten_publishers = graphene.List(graphene.NonNull(ExploreStastOrganizationType))
    top_ten_frameworks = graphene.List(graphene.NonNull(ExploreDeepStatTopActiveFrameworksType))
    top_ten_projects_by_users = graphene.List(graphene.NonNull(ExploreDeepStatTopProjectType))
    top_ten_projects_by_entries = graphene.List(graphene.NonNull(ExploreDeepStatTopProjectEntryType))

    leads_count_by_month = graphene.Field(ExploreCountByDateListType)
    leads_count_by_day = graphene.Field(ExploreCountByDateListType)

    entries_count_by_month = graphene.Field(ExploreCountByDateListType)
    entries_count_by_day = graphene.Field(ExploreCountByDateListType)
    entries_count_by_region = graphene.List(graphene.NonNull(ExploreDeepStatEntriesCountByCentroidType))

    projects_by_region = graphene.List(ExploreDashboardProjectRegion)
    projects_count_by_month = graphene.Field(ExploreCountByDateListType)
    projects_count_by_day = graphene.Field(ExploreCountByDateListType)

    # --- Numeric data ----
    @staticmethod
    @node_cache(CacheKey.ExploreDeep.TOTAL_PROJECTS_COUNT)
    def resolve_total_projects(root: ExploreDashboardStatRoot, *_) -> int:
        return root.projects_qs.count()

    @staticmethod
    @node_cache(CacheKey.ExploreDeep.TOTAL_REGISTERED_USERS_COUNT)
    def resolve_total_registered_users(root: ExploreDashboardStatRoot, *_) -> int:
        return root.registered_users.filter(is_active=True).count()

    @staticmethod
    @node_cache(CacheKey.ExploreDeep.TOTAL_LEADS_COUNT)
    def resolve_total_leads(root: ExploreDashboardStatRoot, *_) -> int:
        return root.leads_qs.count()

    @staticmethod
    @node_cache(CacheKey.ExploreDeep.TOTAL_ENTRIES_COUNT)
    def resolve_total_entries(root: ExploreDashboardStatRoot, *_) -> int:
        return root.entries_qs.count()

    @staticmethod
    @CacheHelper.gql_cache(CacheKey.ExploreDeep.TOTAL_ENTRIES_ADDED_LAST_WEEK_COUNT, timeout=NODE_CACHE_TIMEOUT)
    def resolve_total_entries_added_last_week(*_) -> int:
        return Entry.objects.filter(
            created_at__gte=timezone.now().date() - timedelta(days=7)
        ).count()

    @staticmethod
    @node_cache(CacheKey.ExploreDeep.TOTAL_ACTIVE_USERS_COUNT)
    def resolve_total_active_users(root: ExploreDashboardStatRoot, *_) -> int:
        return root.leads_qs.values('created_by').union(
            root.entries_qs.values('created_by')
        ).count()

    @staticmethod
    @node_cache(CacheKey.ExploreDeep.TOTAL_AUTHORS_COUNT)
    def resolve_total_authors(root: ExploreDashboardStatRoot, *_) -> int:
        return root.leads_qs.values('authors').distinct().count()

    @staticmethod
    @node_cache(CacheKey.ExploreDeep.TOTAL_PUBLISHERS_COUNT)
    def resolve_total_publishers(root: ExploreDashboardStatRoot, *_) -> int:
        return root.leads_qs.values('source').distinct().count()

    # --- Array data ----
    @staticmethod
    @node_cache(CacheKey.ExploreDeep.TOP_TEN_AUTHORS_LIST)
    def resolve_top_ten_authors(root: ExploreDashboardStatRoot, *_):
        return get_top_ten_organizations_list(root.organization_qs, root.leads_qs, root.projects_qs, 'authors')

    @staticmethod
    @node_cache(CacheKey.ExploreDeep.TOP_TEN_PUBLISHERS_LIST)
    def resolve_top_ten_publishers(root: ExploreDashboardStatRoot, *_):
        return get_top_ten_organizations_list(root.organization_qs, root.leads_qs, root.projects_qs, 'source')

    @staticmethod
    @node_cache(CacheKey.ExploreDeep.TOP_TEN_FRAMEWORKS_LIST)
    def resolve_top_ten_frameworks(root: ExploreDashboardStatRoot, *_):
        projects_count_by_af = {
            af: count
            for af, count in root.projects_qs.filter(
                analysis_framework__in=root.analysis_framework_qs
            ).order_by().values('analysis_framework').annotate(
                count=models.Count('id'),
            ).values_list('analysis_framework', 'count')
        }
        entries_count_by_af = {
            af: count
            for af, count in root.entries_qs.filter(
                analysis_framework__in=root.analysis_framework_qs
            ).order_by().values('analysis_framework').annotate(
                count=models.Count('id'),
            ).values_list('analysis_framework', 'count')
        }
        af_count_data = sorted([
            (af_id, entries_count_by_af.get(af_id, 0), projects_count_by_af.get(af_id, 0))
            for af_id in set([*projects_count_by_af.keys(), *entries_count_by_af.keys()])
        ], key=lambda x: x[1:], reverse=True)[:10]
        af_data = {
            af['id']: af
            for af in root.analysis_framework_qs.distinct().filter(
            ).values(
                'id',
                'title',
            )
        }
        return [
            {
                **af_data[af_id],
                'entries_count': entries_count,
                'projects_count': projects_count,
            }
            for af_id, entries_count, projects_count in af_count_data
            if af_id in af_data
        ]

    @staticmethod
    @node_cache(CacheKey.ExploreDeep.TOP_TEN_PROJECTS_BY_USERS_LIST)
    def resolve_top_ten_projects_by_users(root: ExploreDashboardStatRoot, *_):
        return list(
            root.projects_qs.distinct().annotate(
                users_count=models.functions.Coalesce(
                    models.Subquery(
                        ProjectMembership.objects.filter(
                            project=models.OuterRef('pk')
                        ).order_by().values('project').annotate(
                            count=models.Count('member', distinct=True),
                        ).values('count')[:1],
                        output_field=models.IntegerField()
                    ), 0),
            ).order_by('-users_count').values(
                'id',
                'title',
                'users_count',
            )[:10]
        )

    @staticmethod
    @node_cache(CacheKey.ExploreDeep.TOP_TEN_PROJECTS_BY_ENTRIES_LIST)
    def resolve_top_ten_projects_by_entries(root: ExploreDashboardStatRoot, *_):
        return list(
            root.projects_qs.distinct().annotate(
                leads_count=models.functions.Coalesce(
                    models.Subquery(
                        root.leads_qs.filter(
                            project=models.OuterRef('pk')
                        ).order_by().values('project').annotate(
                            count=models.Count('id', distinct=True),
                        ).values('count')[:1],
                        output_field=models.IntegerField()
                    ), 0),
                entries_count=models.functions.Coalesce(
                    models.Subquery(
                        # TODO: Use global filers
                        root.entries_qs.filter(
                            project=models.OuterRef('pk')
                        ).order_by().values('project').annotate(
                            count=models.Count('id', distinct=True),
                        ).values('count')[:1],
                        output_field=models.IntegerField()
                    ), 0),
            ).order_by('-entries_count', '-leads_count').values(
                'id',
                'title',
                'leads_count',
                'entries_count',
            )[:10]
        )

    # --- Time-series data ----
    @staticmethod
    def resolve_leads_count_by_month(root: ExploreDashboardStatRoot, *_):
        return count_by_date_queryset_generator(root.leads_qs, TruncMonth)

    @staticmethod
    def resolve_leads_count_by_day(root: ExploreDashboardStatRoot, *_):
        return count_by_date_queryset_generator(root.leads_qs, TruncDay)

    @staticmethod
    def resolve_entries_count_by_month(root: ExploreDashboardStatRoot, *_):
        return count_by_date_queryset_generator(root.entries_qs, TruncDay)

    @staticmethod
    def resolve_entries_count_by_day(root: ExploreDashboardStatRoot, *_):
        return count_by_date_queryset_generator(root.entries_qs, TruncDay)

    @staticmethod
    def resolve_entries_count_by_region(root: ExploreDashboardStatRoot, *_):
        return root.entries_count_by_geo_area_aggregate_qs\
            .order_by().values('geo_area').annotate(
                count=models.Sum('entries_count'),
            ).values(
                'count',
                centroid=models.F('geo_area__centroid'),
            )

    @staticmethod
    def resolve_projects_by_region(root: ExploreDashboardStatRoot, *_):
        return Region.objects.annotate(
            project_ids=ArrayAgg(
                'project',
                distinct=True,
                ordering='project',
                filter=models.Q(project__in=root.projects_qs),
            ),
        ).filter(project_ids__isnull=False).values(
            'id',
            'centroid',
            'project_ids',
        )

    @staticmethod
    def resolve_projects_count_by_month(root: ExploreDashboardStatRoot, *_):
        return count_by_date_queryset_generator(root.projects_qs, TruncMonth)

    @staticmethod
    def resolve_projects_count_by_day(root: ExploreDashboardStatRoot, *_):
        return count_by_date_queryset_generator(root.projects_qs, TruncDay)

    @staticmethod
    def custom_resolver(request, _filter):
        """
        This is used as root for other resovler
        """
        # Without global filters, to be used for related models
        ref_projects_qs = ExploreProjectFilterSet(
            request=request,
            queryset=project_queryset(),
            data=_filter.get('project'),
        ).qs

        projects_qs = copy.deepcopy(ref_projects_qs).filter(**get_global_filters(_filter))
        organization_qs = Organization.objects.filter(**get_global_filters(_filter))
        analysis_framework_qs = AnalysisFramework.objects.filter(**get_global_filters(_filter))
        registered_users = User.objects.filter(**get_global_filters(_filter, date_field='date_joined'))

        # With ref_projects_qs as filter
        entries_qs = Entry.objects.filter(**get_global_filters(_filter), project__in=ref_projects_qs)
        leads_qs = Lead.objects.filter(**get_global_filters(_filter), project__in=ref_projects_qs)
        entries_count_by_geo_area_aggregate_qs = EntriesCountByGeoAreaAggregate.objects\
            .filter(
                **get_global_filters(_filter, date_field='date'),
                project__in=ref_projects_qs,
                geo_area__centroid__isempty=False,
            )

        cache_key = CacheHelper.generate_hash(_filter.__dict__)
        return ExploreDashboardStatRoot(
            cache_key=cache_key,
            ref_projects_qs=ref_projects_qs,
            projects_qs=projects_qs,
            analysis_framework_qs=analysis_framework_qs,
            organization_qs=organization_qs,
            registered_users=registered_users,
            entries_qs=entries_qs,
            leads_qs=leads_qs,
            entries_count_by_geo_area_aggregate_qs=entries_count_by_geo_area_aggregate_qs,
        )


class PublicExploreYearSnapshotType(DjangoObjectType):
    class Meta:
        model = PublicExploreYearSnapshot
        only_fields = (
            'id',
            'year',
        )
    file = graphene.Field(FileFieldType)


class Query:
    deep_explore_stats = graphene.Field(
        ExploreDashboardStatType,
        filter=ExploreDeepFilterInputType(required=True)
    )
    public_deep_explore_yearly_snapshots = DjangoListField(PublicExploreYearSnapshotType)

    @staticmethod
    def resolve_deep_explore_stats(_, info, filter):
        return ExploreDashboardStatType.custom_resolver(info.context.request, filter)
