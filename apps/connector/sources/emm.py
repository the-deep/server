import re
import requests
from lxml import etree

from django.db import transaction

from utils.common import random_key, get_ns_tag

from lead.models import Lead, LeadEMMTrigger, EMMEntity
from .rss_feed import RssFeed

import logging
logger = logging.getLogger(__name__)


class EMM(RssFeed):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Sets up conf
        self.initialize()

    def initialize(self):
        from connector.models import EMMConfig
        conf = EMMConfig.objects.all().first()
        if not conf:
            msg = 'There is no configuration for emm connector'
            logger.error(msg)
            raise Exception(msg)
        self.conf = conf
        self.conf.trigger_regex = re.compile(self.conf.trigger_regex)

    def fetch(self, params, offset=None, limit=None):
        results = []
        if not params or not params.get('feed-url'):
            return results, 0

        r = requests.get(params['feed-url'])

        return self.parse_xml(r.content, offset, limit)

    def parse_xml(self, content, params, offset, limit):
        xml = etree.fromstring(content)
        # SET NSMAP
        self.nsmap = xml.nsmap
        items = xml.findall('channel/item')

        limited_items = items[(offset or 0):limit] if limit else items
        entities = {}
        leads_infos = []  # Contains kwargs dict
        for item in limited_items:
            # Extract info from item
            lead_info = self.parse_emm_item(item, params)

            item_entities = lead_info.pop('entities', {})
            item_triggers = lead_info.pop('triggers', [])

            entities.update(item_entities)

            leads_infos.append({
                'id': random_key(),
                'source_type': Lead.EMM,
                'emm_triggers': [LeadEMMTrigger(**x) for x in item_triggers],
                'emm_entities': item_entities,
                **lead_info,
            })

        # Get or create EMM entities
        with transaction.atomic():
            for eid, val in entities.items():
                obj, _ = EMMEntity.objects.get_or_create(
                    provider='emm',
                    provider_id=eid,
                    name=val,
                )
                entities[eid] = obj

        # Now create leads(not in db)
        leads = []
        for leadinfo in leads_infos:
            leadinfo['emm_entities'] = [entities[eid] for eid, _ in leadinfo['emm_entities'].items()]
            lead = Lead(*leadinfo)
            lead._emm_entities = leadinfo['emm_entities']
            lead._emm_triggers = leadinfo['emm_triggers']
            leads.append(lead)
        return leads

    def parse_emm_item(self, item, params):
        info = {}
        for lead_field, field in self.option_lead_field_map.items():
            element = item.find(params.get(field, ''))
            info[lead_field] = '' if element is None else element.text or element.get('href')

        # Parse entities
        info['entities'] = self.get_entities(item, self.conf.entity_tag)

        # Parse Triggers
        info['triggers'] = self.get_triggers(item, self.conf.trigger_tag)
        return info

    def get_entities(self, item, entity_tag):
        tag = get_ns_tag(self.nsmap, entity_tag)
        entities = item.findall(tag) or []
        return {
            x.get('id'): x.get('name')
            for x in entities
        }

    def get_triggers(self, item, trigger_tag):
        tag = get_ns_tag(self.nsmap, trigger_tag)
        trigger_elems = item.findall(tag) or []
        triggers = []
        for trigger_elem in trigger_elems:
            trigger_value = trigger_elem.get(get_ns_tag(self.nsmap, self.conf.trigger_attribute))
            if trigger_value is None:
                continue
            raw_triggers = trigger_value.split(self.conf.trigger_separator)
            for raw in raw_triggers:
                trigger = self.parse_trigger(raw)
                triggers.append(trigger) if trigger is not None else None

        return triggers

    def parse_trigger(self, raw):
        match = self.conf.trigger_regex.match(raw)
        if match:
            return {
                'emm_risk_factor': match['risk_factor'],
                'emm_keyword': match['keyword'],
                'count': match['count'],
            }
        return None


def test_emm():
    with open('/tmp/rss.xml') as f:
        e = EMM()
        params = {
            'website-field': 'link',
            'url-field': 'link',
            'date-field': 'pubDate',
            'source-field': 'source',
            'author-field': 'source',
            'title-field': 'title',
        }
        data = e.parse_xml(bytes(f.read(), 'utf-8'), params, 0, 10)
    return data
