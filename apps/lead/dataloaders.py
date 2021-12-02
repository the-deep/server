from promise import Promise
from collections import defaultdict

from django.utils.functional import cached_property
from django.db import models

from utils.graphene.dataloaders import DataLoaderWithContext, WithContextMixin

from entry.models import Entry
from organization.models import Organization
from .models import Lead, LeadPreview, LeadGroup


class LeadPreviewLoader(DataLoaderWithContext):
    def batch_load_fn(self, keys):
        lead_preview_qs = LeadPreview.objects.filter(lead__in=keys)
        _map = {
            lead_preview.lead_id: lead_preview
            for lead_preview in lead_preview_qs
        }
        return Promise.resolve([_map.get(key) for key in keys])


class EntriesCountLoader(DataLoaderWithContext):
    def batch_load_fn(self, keys):
        active_af = self.context.active_project.analysis_framework
        stat_qs = Entry.objects\
            .filter(lead__in=keys)\
            .order_by('lead').values('lead')\
            .annotate(
                total=models.functions.Coalesce(
                    models.Count(
                        'id',
                        filter=models.Q(analysis_framework=active_af)
                    ),
                    0,
                ),
                controlled=models.functions.Coalesce(
                    models.Count(
                        'id',
                        filter=models.Q(controlled=True, analysis_framework=active_af)
                    ),
                    0,
                ),
            ).values('lead_id', 'total', 'controlled')
        _map = {
            stat.pop('lead_id'): stat
            for stat in stat_qs
        }
        _dummy = {
            'total': 0,
            'controlled': 0,
        }
        return Promise.resolve([_map.get(key, _dummy) for key in keys])


class LeadGroupLeadCountLoader(DataLoaderWithContext):
    def batch_load_fn(self, keys):
        lead_group_qs = LeadGroup.objects.filter(id__in=keys).annotate(
            lead_counts=models.Count('lead', distinct=True)
        )
        _map = {
            id: count
            for id, count in lead_group_qs.values_list('id', 'lead_counts')
        }
        return Promise.resolve([_map.get(key, 0) for key in keys])


class LeadSourceLoader(DataLoaderWithContext):
    def batch_load_fn(self, keys):
        organization_qs = Organization.objects.filter(id__in=keys)
        _map = {
            org.pk: org for org in organization_qs
        }
        return Promise.resolve([_map.get(key) for key in keys])


class LeadAuthorsLoader(DataLoaderWithContext):
    def batch_load_fn(self, keys):
        lead_author_qs = Lead.objects\
            .filter(id__in=keys, authors__isnull=False)\
            .values_list('id', 'authors__id')
        lead_author_map = defaultdict(list)
        organizations_id = set()
        for lead_id, author_id in lead_author_qs:
            lead_author_map[lead_id].append(author_id)
            organizations_id.add(author_id)

        organization_qs = Organization.objects.filter(id__in=organizations_id)
        _map = {
            org.id: org for org in organization_qs
        }
        return Promise.resolve([
            [
                _map.get(author)
                for author in lead_author_map.get(key, [])
            ]
            for key in keys
        ])


class DataLoaders(WithContextMixin):
    @cached_property
    def lead_preview(self):
        return LeadPreviewLoader(context=self.context)

    @cached_property
    def entries_counts(self):
        return EntriesCountLoader(context=self.context)

    @cached_property
    def leadgroup_lead_counts(self):
        return LeadGroupLeadCountLoader(context=self.context)

    @cached_property
    def source_organization(self):
        return LeadSourceLoader(context=self.context)

    @cached_property
    def author_organizations(self):
        return LeadAuthorsLoader(context=self.context)
