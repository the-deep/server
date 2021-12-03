from collections import defaultdict

from promise import Promise
from django.core.cache import cache
from django.utils.functional import cached_property
from django.db import models
from django.contrib.postgres.fields.jsonb import KeyTextTransform
from django.contrib.postgres.aggregates.general import ArrayAgg
from django.db.models.functions import Cast
from django.utils import timezone

from deep.caches import CacheKey
from utils.common import get_number_of_months_between_dates
from utils.graphene.dataloaders import DataLoaderWithContext, WithContextMixin

from lead.models import Lead
from entry.models import Entry
from export.models import Export
from user.models import User
from geo.models import Region
from analysis_framework.models import AnalysisFramework

from .models import (
    Project,
    ProjectJoinRequest,
    ProjectOrganization,
)


class ProjectStatLoader(DataLoaderWithContext):
    def batch_load_fn(self, keys):
        annotate_data = {
            key: Cast(KeyTextTransform(key, 'stats_cache'), models.IntegerField())
            for key in [
                'number_of_leads',
                'number_of_leads_not_tagged',
                'number_of_leads_in_progress',
                'number_of_leads_tagged',
                'number_of_entries',
                'number_of_entries_verified',
                'number_of_entries_controlled',
                'number_of_users',
            ]
        }
        stat_qs = Project.objects.filter(id__in=keys).annotate(**annotate_data)
        _map = {
            project_with_stat.id: project_with_stat
            for project_with_stat in stat_qs
        }
        return Promise.resolve([_map.get(key) for key in keys])


class ProjectJoinStatusLoader(DataLoaderWithContext):
    def batch_load_fn(self, keys):
        join_status_qs = ProjectJoinRequest.objects.filter(
            project__in=keys,
            requested_by=self.context.request.user,
            status='pending',
        ).values_list('project_id', flat=True)
        _map = {
            project_id: True
            for project_id in join_status_qs
        }
        return Promise.resolve([_map.get(key, False) for key in keys])


class OrganizationsLoader(DataLoaderWithContext):
    def batch_load_fn(self, keys):
        qs = ProjectOrganization.objects.filter(project__in=keys)
        _map = defaultdict(list)
        for org in qs.all():
            _map[org.project_id].append(org)
        return Promise.resolve([_map.get(key) for key in keys])


class ProjectExploreStatsLoader(WithContextMixin):
    def get_stats(self):
        now = timezone.now()

        # Projects -- stats_cache__entries_activity are calculated for last 3 months
        project_count = Project.objects.count()
        latest_active_projects_qs = Project.objects\
            .filter(is_private=False)\
            .order_by('-stats_cache__entries_activity', '-created_at')
        latest_active_projects = latest_active_projects_qs\
            .values(
                'analysis_framework_id',
                project_id=models.F('id'),
                project_title=models.F('title'),
                analysis_framework_title=models.F('analysis_framework__title'),
            )[:5]
        # All leads
        leads_qs = Lead.objects.all()
        leads_count = leads_qs.count()
        lead_created_at_range = leads_qs.aggregate(
            max_created_at=models.Max('created_at'),
            min_created_at=models.Min('created_at'),
        )
        # Tagged leads
        tagged_leads_qs = leads_qs.annotate(
            entries_count=models.Subquery(
                Entry.objects.filter(
                    lead=models.OuterRef('pk'),
                ).order_by().values('lead').annotate(count=models.Count('id')).values('count')[:1],
                output_field=models.IntegerField()
            ),
        ).filter(entries_count__gt=0)
        tagged_leads_count = tagged_leads_qs.count()
        tagged_lead_created_at_range = tagged_leads_qs.aggregate(
            max_created_at=models.Max('created_at'),
            min_created_at=models.Min('created_at'),
        )
        # Exports
        exports_count = Export.objects.count()
        exports_created_at_range = Export.objects.aggregate(
            max_exported_at=models.Max('exported_at'),
            min_exported_at=models.Min('exported_at'),
        )

        # Recent frameworks
        top_active_frameworks = AnalysisFramework.objects.filter(is_private=False).annotate(
            project_count=models.functions.Coalesce(
                models.Subquery(
                    Project.objects.filter(
                        analysis_framework=models.OuterRef('pk')
                    ).order_by().values('analysis_framework').annotate(
                        count=models.Count('id', distinct=True),
                    ).values('count')[:1],
                    output_field=models.IntegerField()
                ), 0),
            source_count=models.functions.Coalesce(
                models.Subquery(
                    Lead.objects.filter(
                        project__analysis_framework=models.OuterRef('pk')
                    ).order_by().values('project__analysis_framework').annotate(
                        count=models.Count('id', distinct=True)
                    ).values('count')[:1],
                    output_field=models.IntegerField()
                ), 0),
        ).order_by('-project_count', '-source_count').values(
            analysis_framework_id=models.F('id'),
            analysis_framework_title=models.F('title'),
            project_count=models.F('project_count'),
            source_count=models.F('source_count'),
        )[:5]

        return dict(
            calculated_at=now,
            total_projects=project_count,
            total_users=User.objects.filter(is_active=True).count(),
            leads_added_weekly=leads_count and (
                leads_count / (
                    (
                        (
                            abs(
                                lead_created_at_range['max_created_at'] - lead_created_at_range['min_created_at']
                            ).days
                        ) // 7
                    ) or 1
                )
            ),
            daily_average_leads_tagged_per_project=tagged_leads_count and (
                tagged_leads_count / (
                    (
                        abs(
                            tagged_lead_created_at_range['max_created_at'] - tagged_lead_created_at_range['min_created_at']
                        ).days
                    ) or 1
                ) / (project_count or 1)
            ),
            generated_exports_monthly=exports_count and (
                exports_count / (
                    get_number_of_months_between_dates(
                        exports_created_at_range['max_exported_at'],
                        exports_created_at_range['min_exported_at']
                    ) or 1
                )
            ),
            top_active_projects=latest_active_projects,
            top_active_frameworks=top_active_frameworks,
        )

    def resolve(self):
        return cache.get_or_set(
            CacheKey.PROJECT_EXPLORE_STATS_LOADER_KEY,
            self.get_stats,
            60 * 60,  # 1hr
        )


class GeoRegionLoader(DataLoaderWithContext):
    @staticmethod
    def get_region_queryset():
        return Region.objects.all()

    def batch_load_fn(self, keys):
        qs = self.get_region_queryset().filter(project__in=keys).annotate(
            projects_id=ArrayAgg('project', filter=models.Q(project__in=keys)),
        ).defer('geo_options')
        _map = defaultdict(list)
        for region in qs.all():
            for project_id in region.projects_id:
                _map[project_id].append(region)
        return Promise.resolve([_map.get(key) for key in keys])


class PublicGeoRegionLoader(GeoRegionLoader):
    @staticmethod
    def get_region_queryset():
        return Region.objects.filter(public=True)


class DataLoaders(WithContextMixin):

    @cached_property
    def project_stat(self):
        return ProjectStatLoader(context=self.context)

    @cached_property
    def join_status(self):
        return ProjectJoinStatusLoader(context=self.context)

    @cached_property
    def organizations(self):
        return OrganizationsLoader(context=self.context)

    def resolve_explore_stats(self):
        return ProjectExploreStatsLoader(context=self.context).resolve()

    @cached_property
    def geo_region(self):
        return GeoRegionLoader(context=self.context)

    @cached_property
    def public_geo_region(self):
        return PublicGeoRegionLoader(context=self.context)
