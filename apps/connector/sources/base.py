from functools import reduce
from abc import ABC, abstractmethod
from django.db.models import Q

from organization.models import Organization
from utils.common import random_key

from lead.models import Lead


class OrganizationSearch():
    def __init__(self, texts):
        self.fetch(texts)

    def create_organization(self, text):
        return Organization.objects.create(
            title=text,
            short_name=text,
            long_name=text,
        )

    def fetch(self, texts):
        text_queries = [
            (text, text.lower())
            for text in set(texts) if text
        ]

        if len(text_queries) == 0:
            # Nothing to do here
            self.organization_map = {}
            return

        exact_query = reduce(
            lambda acc, item: acc | item,
            [
                Q(title__iexact=d) |
                Q(short_name__iexact=d) |
                Q(long_name__iexact=d)
                for _, d in text_queries
            ],
        )
        exact_organizations = Organization.objects.filter(exact_query).all()
        organization_map = {
            key.lower(): organization
            for organization in exact_organizations
            for key in [organization.title, organization.short_name, organization.long_name]
        }

        # For remaining organizations
        for label, org_text in text_queries:
            if org_text in organization_map:
                continue
            organization_map[org_text] = self.create_organization(label)

        self.organization_map = organization_map
        return self.organization_map

    def get(self, text):
        if text:
            return self.organization_map.get(text.lower())


class Source(ABC):
    DEFAULT_PER_PAGE = 25

    def __init__(self):
        if not hasattr(self, 'title') \
                or not hasattr(self, 'key') \
                or not hasattr(self, 'options'):
            raise Exception('Source not defined properly')

    @abstractmethod
    def fetch(self, params, offset=None, limit=None):
        pass

    def get_leads(self, *args, **kwargs):
        leads_data, total_count = self.fetch(*args, **kwargs)
        if not leads_data:
            return [], total_count

        organization_search = OrganizationSearch([
            label
            for d in leads_data
            for label in [d['source'], d['author']]
        ])

        leads = []
        for ldata in leads_data:
            lead = Lead(
                id=ldata.get('id', random_key()),
                title=ldata['title'],
                published_on=ldata['published_on'],
                url=ldata['url'],
                source_raw=ldata['source'],
                author_raw=ldata['author'],
                source=organization_search.get(ldata['source']),
                author=organization_search.get(ldata['author']),
                source_type=ldata['source_type'],
                website=ldata['website'],
            )

            # Add emm info
            if ldata.get('emm_triggers') is not None:
                lead._emm_triggers = ldata['emm_triggers']
            if ldata.get('emm_entities') is not None:
                lead._emm_entities = ldata['emm_entities']

            leads.append(lead)

        return leads, total_count

    def query_leads(self, params, offset, limit):
        from connector.serializers import SourceDataSerializer

        if offset is None or offset < 0:
            offset = 0
        if not limit or limit < 0:
            limit = Source.DEFAULT_PER_PAGE

        data, total_count = self.get_leads(params, offset, limit)
        return SourceDataSerializer(
            data,
            many=True,
        ).data
