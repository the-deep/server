import copy
import datetime
from abc import ABC, abstractmethod
from functools import reduce
from typing import List, Tuple, Union

from django.db.models import Q
from lead.models import Lead
from organization.models import Organization

from utils.common import random_key
from utils.date_extractor import str_to_date


class OrganizationSearch:
    def __init__(self, texts, source_type, creator):
        self.source_type = source_type
        self.creator = creator
        self.fetch(texts)

    def create_organization(self, text):
        return Organization.objects.create(
            title=text,
            short_name=text,
            long_name=text,
            source=self.source_type,
            created_by=self.creator,
        )

    def fetch(self, texts):
        text_queries = [(text, text.lower()) for text in set(texts) if text]

        if len(text_queries) == 0:
            # Nothing to do here
            self.organization_map = {}
            return

        exact_query = reduce(
            lambda acc, item: acc | item,
            [Q(title__iexact=d) | Q(short_name__iexact=d) | Q(long_name__iexact=d) for _, d in text_queries],
        )
        exact_organizations = Organization.objects.filter(exact_query).select_related("parent").all()
        organization_map = {
            # NOTE: organization.data will return itself or it's parent organization (handling merged organizations)
            key.lower(): organization.data
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
    UNIFIED_CONNECTOR_SOURCE_MAX_PAGE_NUMBER = 100

    def __init__(self):
        if not hasattr(self, "title") or not hasattr(self, "key") or not hasattr(self, "options"):
            raise Exception("Source not defined properly")

    @abstractmethod
    def fetch(self, params):
        return [], 0

    def get_leads(self, params, request_user) -> Tuple[List[Lead], int]:
        def _parse_date(date_raw) -> Union[None, datetime.date]:
            if isinstance(date_raw, datetime.date):
                return date_raw
            elif isinstance(date_raw, datetime.datetime):
                return date_raw.date()
            else:
                published_on = str_to_date(date_raw)
                if published_on:
                    return published_on.date()

        leads_data, total_count = self.fetch(copy.deepcopy(params))
        if not leads_data:
            return [], total_count

        organization_search = OrganizationSearch(
            [label for d in leads_data for label in [d["source"], d["author"]]],
            Organization.SourceType.CONNECTOR,
            request_user,
        )

        leads = []
        for ldata in leads_data:
            published_on = _parse_date(ldata["published_on"])
            lead = Lead(
                id=ldata.get("id", random_key()),
                title=ldata["title"],
                published_on=published_on,
                url=ldata["url"],
                source_raw=ldata["source"],
                author_raw=ldata["author"],
                source=organization_search.get(ldata["source"]),
                author=organization_search.get(ldata["author"]),
                source_type=ldata["source_type"],
            )

            if ldata.get("author") is not None:
                lead._authors = list(filter(None, [organization_search.get(ldata["author"])]))

            # Add emm info
            if ldata.get("emm_triggers") is not None:
                lead._emm_triggers = ldata["emm_triggers"]
            if ldata.get("emm_entities") is not None:
                lead._emm_entities = ldata["emm_entities"]

            leads.append(lead)
        return leads, total_count
