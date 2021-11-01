from promise import Promise
from django.utils.functional import cached_property
from django.db import models

from utils.graphene.dataloaders import DataLoaderWithContext, WithContextMixin

from entry.models import Entry
from .models import LeadPreview, LeadGroup


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


class LeadGroupLoader(DataLoaderWithContext):
    def batch_load_fn(self, keys):
        lead_group_qs = LeadGroup.objects.filter(id__in=keys).annotate(
            lead_counts=models.Count('lead', distinct=True)
        )
        _map = {
            lead_group['id']: lead_group['lead_counts']
            for lead_group in lead_group_qs.values('id', 'lead_counts')
        }
        return Promise.resolve([_map.get(key) for key in keys])


class DataLoaders(WithContextMixin):
    @cached_property
    def lead_preview(self):
        return LeadPreviewLoader(context=self.context)

    @cached_property
    def entries_counts(self):
        return EntriesCountLoader(context=self.context)

    @cached_property
    def lead_counts(self):
        return LeadGroupLoader(context=self.context)
