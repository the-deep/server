from promise import Promise
from django.utils.functional import cached_property
from django.db import models
from django.contrib.postgres.fields.jsonb import KeyTextTransform
from django.db.models.functions import Cast

from utils.graphene.dataloaders import DataLoaderWithContext, WithContextMixin

from project.models import Project, ProjectJoinRequest


class ProjectStatLoader(DataLoaderWithContext):
    def batch_load_fn(self, keys):
        annotate_data = {
            key: Cast(KeyTextTransform(key, 'stats_cache'), models.IntegerField())
            for key in [
                ('number_of_leads'),
                ('number_of_leads_tagged'),
                ('number_of_leads_tagged_and_verified'),
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


class DataLoaders(WithContextMixin):

    @cached_property
    def project_stat(self):
        return ProjectStatLoader(context=self.context)

    @cached_property
    def join_status(self):
        return ProjectJoinStatusLoader(context=self.context)
