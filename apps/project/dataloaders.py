from collections import defaultdict

from promise import Promise
from django.core.cache import cache
from django.utils.functional import cached_property
from django.db import models
from django.contrib.postgres.fields.jsonb import KeyTextTransform
from django.db.models.functions import Cast

from deep.caches import CacheKey
from utils.graphene.dataloaders import DataLoaderWithContext, WithContextMixin

from lead.models import Lead

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
                ('number_of_leads'),
                ('number_of_leads_tagged'),
                ('number_of_leads_tagged_and_controlled'),
                ('number_of_entries'),
                ('number_of_users'),
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
        leads_qs = Lead.objects.all()

        return dict(
            leads_added_weekly=leads_qs.count(),
            daily_average_leads_tagged_per_project=0,
            generated_exports_monthly=0,
            top_active_projects=[
                dict(
                    project_id=1,
                    project_title='Project 1',
                    analysis_framework_id=1,
                    analysis_framework_title='AF 1',
                )
            ],
        )

    def resolve(self):
        return cache.get_or_set(
            CacheKey.PROJECT_EXPLORE_STATS_LOADER_KEY,
            self.get_stats,
            60 * 60 * 30,
        )


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

    @cached_property
    def organization_type_organization(self):
        return OrganizationsLoader(context=self.context)

    def resolve_explore_stats(self):
        return ProjectExploreStatsLoader(context=self.context).resolve()
