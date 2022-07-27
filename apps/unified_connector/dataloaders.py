from collections import defaultdict
from promise import Promise
from django.utils.functional import cached_property
from django.db import models

from utils.graphene.dataloaders import DataLoaderWithContext, WithContextMixin

from organization.models import Organization
from organization.dataloaders import OrganizationLoader

from .models import (
    ConnectorLead,
    ConnectorSourceLead,
    ConnectorSource,
)

DEFAULT_SOURCE_LEAD_COUNT = {'total': 0, 'already_added': 0, 'blocked': 0}


class UnifiedConnectorLeadsCount(DataLoaderWithContext):
    def batch_load_fn(self, keys):
        connector_leads_qs = ConnectorSourceLead.objects\
            .filter(source__unified_connector__in=keys)\
            .order_by().values('source__unified_connector')\
            .annotate(
                count=models.Count('connector_lead', distinct=True),
                already_count=models.Count('connector_lead', distinct=True, filter=models.Q(already_added=True)),
                blocked_count=models.Count('connector_lead', distinct=True, filter=models.Q(blocked=True)),
            )\
            .values_list('source__unified_connector', 'count', 'already_count', 'blocked_count')
        _map = {
            uc: dict(
                total=count or 0,
                already_added=already_count or 0,
                blocked=blocked_count or 0,
            )
            for uc, count, already_count, blocked_count in connector_leads_qs
        }
        return Promise.resolve([_map.get(key, DEFAULT_SOURCE_LEAD_COUNT) for key in keys])


class UnifiedConnectorSources(DataLoaderWithContext):
    def batch_load_fn(self, keys):
        connector_source_qs = ConnectorSource.objects\
            .filter(unified_connector__in=keys)\
            .order_by('id')
        _map = defaultdict(list)
        for connector_source in connector_source_qs:
            _map[connector_source.unified_connector_id].append(connector_source)
        return Promise.resolve([_map[key] for key in keys])


class ConnectorSourceLeadsCount(DataLoaderWithContext):
    def batch_load_fn(self, keys):
        connector_leads_qs = ConnectorSourceLead.objects\
            .filter(source__in=keys)\
            .order_by().values('source')\
            .annotate(
                count=models.Count('connector_lead', distinct=True),
                already_count=models.Count('connector_lead', distinct=True, filter=models.Q(already_added=True)),
                blocked_count=models.Count('connector_lead', distinct=True, filter=models.Q(blocked=True)),
            )\
            .values_list('source', 'count', 'already_count', 'blocked_count')
        _map = {
            uc: dict(
                total=count or 0,
                already_added=already_count or 0,
                blocked=blocked_count or 0,
            )
            for uc, count, already_count, blocked_count in connector_leads_qs
        }
        return Promise.resolve([_map.get(key, DEFAULT_SOURCE_LEAD_COUNT) for key in keys])


class ConnectorSourceLeadLead(DataLoaderWithContext):
    def batch_load_fn(self, keys):
        connector_leads_qs = ConnectorLead.objects\
            .filter(id__in=keys)\
            .order_by('id')
        _map = {
            connector_lead.pk: connector_lead
            for connector_lead in connector_leads_qs
        }
        return Promise.resolve([_map[key] for key in keys])


class ConnectorLeadAuthors(DataLoaderWithContext):
    def batch_load_fn(self, keys):
        connector_lead_author_qs = ConnectorLead.objects\
            .filter(id__in=keys, authors__isnull=False)\
            .order_by('authors__id')\
            .values_list('id', 'authors__id')
        connector_lead_authors_ids = defaultdict(list)
        organizations_id = set()
        for connector_lead_id, author_id in connector_lead_author_qs:
            connector_lead_authors_ids[connector_lead_id].append(author_id)
            organizations_id.add(author_id)

        organization_qs = Organization.objects.filter(id__in=organizations_id)
        organizations_map = {
            org.id: org for org in organization_qs
        }
        return Promise.resolve([
            [
                organizations_map.get(author)
                for author in connector_lead_authors_ids.get(key, [])
            ]
            for key in keys
        ])


class DataLoaders(WithContextMixin):
    @cached_property
    def unified_connector_leads_count(self):
        return UnifiedConnectorLeadsCount(context=self.context)

    @cached_property
    def unified_connector_sources(self):
        return UnifiedConnectorSources(context=self.context)

    @cached_property
    def connector_source_leads_count(self):
        return ConnectorSourceLeadsCount(context=self.context)

    @cached_property
    def connector_source_lead_lead(self):
        return ConnectorSourceLeadLead(context=self.context)

    @cached_property
    def connector_lead_source(self):
        return OrganizationLoader(context=self.context)

    @cached_property
    def connector_lead_authors(self):
        return ConnectorLeadAuthors(context=self.context)
