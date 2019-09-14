from functools import reduce
from abc import ABC, abstractmethod
from django.db.models import Q

from organization.models import Organization
from utils.common import random_key

from lead.models import Lead


class Source(ABC):
    DEFAULT_PER_PAGE = 25

    def __init__(self):
        if not hasattr(self, 'title') \
                or not hasattr(self, 'key') \
                or not hasattr(self, 'options'):
            raise Exception('Source not defined properly')

    @abstractmethod
    def fetch(self, params, page=None, limit=None):
        pass

    def get_leads(self, *args, **kwargs):
        # TODO: If leads_data is empty
        leads_data = self.fetch(*args, **kwargs) or []
        # TODO: LOOK INTO THIS PROCESS
        organization_query = reduce(
            lambda a, b: a | b,
            map(
                lambda d: (
                    # TODO: if value are None
                    Q(title__iexact=d['source']) |
                    Q(title__iexact=d['author']) |
                    Q(short_name__iexact=d['source']) |
                    Q(short_name__iexact=d['author']) |
                    Q(long_name__iexact=d['source']) |
                    Q(long_name__iexact=d['author'])
                ),
                leads_data,
            )
        )
        organizations = Organization.objects.filter(organization_query).all()
        organization_map = {
            organization.title: organization
            for organization in organizations
        }
        organization_map.update({
            organization.short_name: organization
            for organization in organizations
        })
        leads = []
        for ldata in leads_data:
            lead = Lead(
                id=ldata.get('id', random_key()),
                title=ldata['title'],
                published_on=ldata['published_on'],
                url=ldata['url'],
                source_raw=ldata['source'],
                author_raw=ldata['author'],
                source=organization_map.get(ldata['source']),
                author=organization_map.get(ldata['author']),
                source_type=ldata['source_type'],
                website=ldata['website'],
            )

            # Add emm info
            if ldata.get('emm_triggers') is not None:
                lead._emm_triggers = ldata['emm_triggers']
            if ldata.get('emm_entities') is not None:
                lead._emm_entities = ldata['emm_entities']

            leads.append(lead)

        return leads, len(leads)

    def query_leads(self, params, limit=None, offset=None):
        from connector.serializers import SourceDataSerializer

        if offset is None or offset < 0:
            offset = 0
        if not limit or limit < 0:
            limit = Source.DEFAULT_PER_PAGE

        data = self.get_leads(params)[0]
        return SourceDataSerializer(
            data[offset:offset + limit],
            many=True,
        ).data
