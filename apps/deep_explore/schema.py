import copy
import graphene
from dataclasses import dataclass

from graphene_django import DjangoObjectType
from django.db import models
from django.db.models.functions import (
    TruncMonth,
    TruncDay,
)
from django.contrib.postgres.aggregates.general import ArrayAgg

from deep.caches import CacheKey, CacheHelper
from utils.graphene.geo_scalars import PointScalar
from organization.models import Organization
from geo.models import Region
from user.models import User
from project.models import Project, ProjectMembership
from lead.models import Lead
from entry.models import Entry
from analysis_framework.models import AnalysisFramework
from deep_explore.models import EntriesCountByGeoAreaAggregate

from project.filter_set import ExploreProjectFilterDataInputType, ExploreProjectFilterSet


class ExploreCountByDateType(graphene.ObjectType):
    date = graphene.Date(required=True)
    count = graphene.Int(required=True)


ExploreCountByDateListType = graphene.List(graphene.NonNull(ExploreCountByDateType))


# TODO?
NODE_CACHE_TIMEOUT = 60 * 5  # 5 min


def node_cache(cache_key):
    def cache_key_gen(root: ExploreDashboardStatRoot, *_):
        return root.cache_key

    return CacheHelper.gql_cache(
        cache_key,
        timeout=NODE_CACHE_TIMEOUT,
        cache_key_gen=cache_key_gen,
    )


def count_by_type_generator(type_name):
    return graphene.List(
        graphene.NonNull(
            type(type_name, (graphene.ObjectType,), {
                'date': graphene.Date(required=True),
                'count': graphene.Int(required=True),
            })
        )
    )


def count_by_date_queryset_generator(qs, trunc_func):
    # Used by ExploreCountByDateListType
    return qs.values(
        date=trunc_func('created_at')
    ).annotate(
        count=models.Count('id')
    ).order_by('date')


def get_top_ten_organizations_list(queryset, lead_field):
    return [
        {
            **org,
            'id': org.pop('_id'),
            'title': org.pop('_title'),
        }
        for org in queryset.annotate(
            _id=models.functions.Coalesce(models.F('parent'), models.F('id')),
            _title=models.functions.Coalesce(models.F('parent__title'), models.F('title')),
        ).annotate(
            leads_count=models.functions.Coalesce(models.Subquery(
                # TODO: Use global filers
                Lead.objects.filter(
                    **{lead_field: models.OuterRef('_id')}
                ).order_by().values(lead_field)
                .annotate(cnt=models.Count('*')).values('cnt')[:1],
                output_field=models.IntegerField(),
            ), 0),
            projects_count=models.functions.Coalesce(models.Subquery(
                # TODO: Use global filers
                Lead.objects.filter(
                    **{lead_field: models.OuterRef('_id')}
                ).order_by().values(lead_field)
                .annotate(cnt=models.Count('project_id', distinct=True)).values('cnt')[:1],
                output_field=models.IntegerField(),
            ), 0),
        ).order_by('-leads_count', '-projects_count').values(
            'leads_count',
            'projects_count',
            # Fetch parent data if available (merged_as)
            '_id',
            '_title',
        ).distinct()[:10]
    ]


class ExploreDeepFilter(graphene.InputObjectType):
    date_from = graphene.DateTime(required=True)
    date_to = graphene.DateTime(required=True)
    project = ExploreProjectFilterDataInputType()


class ExploreStastOrganizationType(graphene.ObjectType):
    id = graphene.ID(required=True)
    title = graphene.String(required=True)
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
    projects_qs: models.QuerySet
    ref_projects_qs: models.QuerySet  # Without global filters


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
    @node_cache(CacheKey.ExploreDeep.TOTAL_PROJECTS)
    def resolve_total_projects(root: ExploreDashboardStatRoot, *_) -> int:
        return root.projects_qs.count()

    @staticmethod
    @node_cache(CacheKey.ExploreDeep.TOTAL_REGISTERED_USERS)
    def resolve_total_registered_users(*_) -> int:
        return User.objects.filter(is_active=True).count()

    @staticmethod
    @node_cache(CacheKey.ExploreDeep.TOTAL_LEADS)
    def resolve_total_leads(root: ExploreDashboardStatRoot, *_) -> int:
        return root.leads_qs.count()

    @staticmethod
    @node_cache(CacheKey.ExploreDeep.TOTAL_ENTRIES)
    def resolve_total_entries(root: ExploreDashboardStatRoot, *_) -> int:
        return root.entries_qs.count()

    @staticmethod
    @node_cache(CacheKey.ExploreDeep.TOTAL_ACTIVE_USERS)
    def resolve_total_active_users(root: ExploreDashboardStatRoot, *_) -> int:
        return root.leads_qs.values('created_by').union(
            root.entries_qs.values('created_by')
        ).count()

    @staticmethod
    @node_cache(CacheKey.ExploreDeep.TOTAL_AUTHORS)
    def resolve_total_authors(root: ExploreDashboardStatRoot, *_) -> int:
        return root.leads_qs.values('authors').distinct().count()

    @staticmethod
    @node_cache(CacheKey.ExploreDeep.TOTAL_PUBLISHERS)
    def resolve_total_publishers(root: ExploreDashboardStatRoot, *_) -> int:
        return root.leads_qs.values('source').distinct().count()

    # --- Array data ----
    @staticmethod
    @node_cache(CacheKey.ExploreDeep.TOP_TEN_AUTHORS)
    def resolve_top_ten_authors(root: ExploreDashboardStatRoot, *_) -> models.QuerySet:
        return get_top_ten_organizations_list(root.organization_qs, 'authors')

    @staticmethod
    @node_cache(CacheKey.ExploreDeep.TOP_TEN_PUBLISHERS)
    def resolve_top_ten_publishers(root: ExploreDashboardStatRoot, *_) -> models.QuerySet:
        return get_top_ten_organizations_list(root.organization_qs, 'source')

    @staticmethod
    @node_cache(CacheKey.ExploreDeep.TOP_TEN_FRAMEWORKS)
    def resolve_top_ten_frameworks(root: ExploreDashboardStatRoot, *_) -> models.QuerySet:
        return list(
            root.analysis_framework_qs.distinct().annotate(
                projects_count=models.functions.Coalesce(
                    models.Subquery(
                        # TODO: Use global filers
                        Project.objects.filter(
                            analysis_framework=models.OuterRef('pk')
                        ).order_by().values('analysis_framework').annotate(
                            count=models.Count('id', distinct=True),
                        ).values('count')[:1],
                        output_field=models.IntegerField()
                    ), 0),
                entries_count=models.functions.Coalesce(
                    models.Subquery(
                        # TODO: Use global filers
                        Entry.objects.filter(
                            project__analysis_framework=models.OuterRef('pk')
                        ).order_by().values('project__analysis_framework').annotate(
                            count=models.Count('id', distinct=True)
                        ).values('count')[:1],
                        output_field=models.IntegerField()
                    ), 0),
            ).order_by('-entries_count', '-projects_count').values(
                'id',
                'title',
                'projects_count',
                'entries_count',
            )[:10]
        )

    @staticmethod
    @node_cache(CacheKey.ExploreDeep.TOP_TEN_PROJECTS_BY_USERS)
    def resolve_top_ten_projects_by_users(root: ExploreDashboardStatRoot, *_) -> models.QuerySet:
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
    @node_cache(CacheKey.ExploreDeep.TOP_TEN_PROJECTS_BY_ENTRIES)
    def resolve_top_ten_projects_by_entries(root: ExploreDashboardStatRoot, *_) -> models.QuerySet:
        return list(
            root.projects_qs.distinct().annotate(
                leads_count=models.functions.Coalesce(
                    models.Subquery(
                        # TODO: Use global filers
                        Lead.objects.filter(
                            project=models.OuterRef('pk')
                        ).order_by().values('project').annotate(
                            count=models.Count('id', distinct=True),
                        ).values('count')[:1],
                        output_field=models.IntegerField()
                    ), 0),
                entries_count=models.functions.Coalesce(
                    models.Subquery(
                        # TODO: Use global filers
                        Entry.objects.filter(
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
    def resolve_leads_count_by_month(root: ExploreDashboardStatRoot, *_) -> models.QuerySet:
        return count_by_date_queryset_generator(root.leads_qs, TruncMonth)

    @staticmethod
    def resolve_leads_count_by_day(root: ExploreDashboardStatRoot, *_) -> models.QuerySet:
        return count_by_date_queryset_generator(root.leads_qs, TruncDay)

    @staticmethod
    def resolve_entries_count_by_month(root: ExploreDashboardStatRoot, *_) -> models.QuerySet:
        return count_by_date_queryset_generator(root.entries_qs, TruncDay)

    @staticmethod
    def resolve_entries_count_by_day(root: ExploreDashboardStatRoot, *_) -> models.QuerySet:
        return count_by_date_queryset_generator(root.entries_qs, TruncDay)

    @staticmethod
    def resolve_entries_count_by_region(root: ExploreDashboardStatRoot, *_) -> models.QuerySet:
        return root.entries_count_by_geo_area_aggregate_qs\
            .order_by().values('geo_area').annotate(
                count=models.Sum('entries_count'),
            ).values(
                'count',
                centroid=models.F('geo_area__centroid'),
            )

    @staticmethod
    def resolve_projects_by_region(root: ExploreDashboardStatRoot, *_) -> models.QuerySet:
        return Region.objects.annotate(
            project_ids=ArrayAgg(
                'project',
                distinct=True,
                ordering='project',
                filter=models.Q(project__in=root.projects_qs),
            ),
        ).filter(project_ids__isnull=False).only('id', 'centroid')

    @staticmethod
    def resolve_projects_count_by_month(root: ExploreDashboardStatRoot, *_) -> models.QuerySet:
        return count_by_date_queryset_generator(root.projects_qs, TruncMonth)

    @staticmethod
    def resolve_projects_count_by_day(root: ExploreDashboardStatRoot, *_) -> models.QuerySet:
        return count_by_date_queryset_generator(root.projects_qs, TruncDay)

    @staticmethod
    def custom_resolver(info, _filter):
        """
        This is used as root for other resovler
        """
        def get_global_filters(date_field='created_at'):
            return {
                f'{date_field}__gte': _filter['date_from'],
                f'{date_field}__lte': _filter['date_to'],
            }

        # Without global filters, to be used for related models
        ref_projects_qs = ExploreProjectFilterSet(
            request=info.context.request,
            data=_filter.get('project'),
        ).qs

        projects_qs = copy.deepcopy(ref_projects_qs).filter(**get_global_filters())
        organization_qs = Organization.objects.filter(**get_global_filters())
        analysis_framework_qs = AnalysisFramework.objects.filter(**get_global_filters())

        # With ref_projects_qs as filter
        entries_qs = Entry.objects.filter(**get_global_filters(), project__in=ref_projects_qs)
        leads_qs = Lead.objects.filter(**get_global_filters(), project__in=ref_projects_qs)
        entries_count_by_geo_area_aggregate_qs = EntriesCountByGeoAreaAggregate.objects\
            .filter(
                **get_global_filters(date_field='date'),
                project__in=ref_projects_qs,
                geo_area__centroid__isempty=False,
            )

        cache_key = CacheHelper.generate_hash(_filter.__dict__)
        return ExploreDashboardStatRoot(
            cache_key=cache_key,
            analysis_framework_qs=analysis_framework_qs,
            entries_count_by_geo_area_aggregate_qs=entries_count_by_geo_area_aggregate_qs,
            entries_qs=entries_qs,
            leads_qs=leads_qs,
            organization_qs=organization_qs,
            projects_qs=projects_qs,
            ref_projects_qs=ref_projects_qs,
        )


class Query:
    deep_explore_stats = graphene.Field(
        ExploreDashboardStatType,
        filter=ExploreDeepFilter(required=True)
    )

    @staticmethod
    def resolve_deep_explore_stats(_, info, filter):
        return ExploreDashboardStatType.custom_resolver(info, filter)
