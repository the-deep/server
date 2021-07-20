from promise import Promise
from django.utils.functional import cached_property
from django.db import models

from utils.graphene.dataloaders import DataLoaderWithContext, WithContextMixin

from entry.models import Entry
from .models import LeadPreview


class LeadPreviewLoader(DataLoaderWithContext):
    def batch_load_fn(self, keys):
        lead_preview_qs = LeadPreview.objects.filter(lead__in=keys)
        _map = {
            lead_preview.lead_id: lead_preview
            for lead_preview in lead_preview_qs
        }
        return Promise.resolve([_map.get(key) for key in keys])


class VerifiedStatLoader(DataLoaderWithContext):
    def batch_load_fn(self, keys):
        stat_qs = Entry.objects\
            .filter(lead__in=keys)\
            .order_by('lead').values('lead')\
            .annotate(
                total_count=models.Count('id'),
                verified_count=models.Count('id', filter=models.Q(verified=True)),
            ).values('lead_id', 'total_count', 'verified_count')
        _map = {
            stat.pop('lead_id'): stat
            for stat in stat_qs
        }
        return Promise.resolve([_map.get(key) for key in keys])


class DataLoaders(WithContextMixin):
    @cached_property
    def lead_preview(self):
        return LeadPreviewLoader(context=self.context)

    @cached_property
    def verified_stat(self):
        return VerifiedStatLoader(context=self.context)
