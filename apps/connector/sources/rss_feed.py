from rest_framework import serializers
from lxml import etree
import requests

from utils.common import DEFAULT_HEADERS, random_key, replace_ns
from lead.models import Lead
from .base import Source


def _get_field_value(item, field):
    if not field:
        return ''
    element = item.find(field)
    return '' if element is None else element.text or element.get('href')


def _get_fields(item, nsmap, parent_tag=None):
    tag = '{}/{}'.format(parent_tag, item.tag) if parent_tag else item.tag
    childs = item.getchildren()
    fields = []
    if len(childs) > 0:
        children_fields = []
        for child in childs:
            children_fields.extend(_get_fields(child, nsmap, tag))
        fields.extend(children_fields)
    else:
        fields.append({
            'key': tag,
            'label': replace_ns(nsmap, tag),
        })
    return fields


class RssFeed(Source):
    title = 'RSS Feed'
    key = 'rss-feed'
    options = [
        {
            'key': 'feed-url',
            'field_type': 'url',
            'title': 'Feed URL'
        },
        {
            'key': 'website-field',
            'field_type': 'select',
            'lead_field': 'website',
            'title': 'Website',
            'options': [],
        },
        {
            'key': 'title-field',
            'field_type': 'select',
            'lead_field': 'title',
            'title': 'Title field',
            'options': [],
        },
        {
            'key': 'date-field',
            'field_type': 'select',
            'lead_field': 'published_on',
            'title': 'Published on field',
            'options': [],
        },
        {
            'key': 'source-field',
            'field_type': 'select',
            'lead_field': 'source',
            'title': 'Publisher field',
            'options': [],
        },
        {
            'key': 'author-field',
            'field_type': 'select',
            'lead_field': 'author',
            'title': 'Author field',
            'options': [],
        },
        {
            'key': 'url-field',
            'field_type': 'select',
            'lead_field': 'url',
            'title': 'URL field',
            'options': [],
        },
    ]

    option_lead_field_map = {
        option['lead_field']: option['key']
        for option in options if option.get('lead_field')
    }

    dynamic_fields = [1, 2, 3, 4, 5]

    def fetch(self, params, offset=None, limit=None):
        results = []
        if not params or not params.get('feed-url'):
            return results, 0

        r = requests.get(params['feed-url'])
        xml = etree.fromstring(r.content)
        items = xml.findall('channel/item')

        for item in items:
            data = Lead(
                id=random_key(),
                source_type=Lead.RSS,
                **{
                    lead_field: _get_field_value(item, params.get(param_key))
                    for lead_field, param_key in self.option_lead_field_map.items()
                },
            )
            results.append(data)

        return results, len(items)

    def query_fields(self, params):
        if not params or not params.get('feed-url'):
            return []

        try:
            r = requests.get(params['feed-url'], headers=DEFAULT_HEADERS)
            xml = etree.fromstring(r.content)
        except requests.exceptions.RequestException:
            raise serializers.ValidationError({
                'feed-url': 'Could not fetch rss feed'
            })
        except etree.XMLSyntaxError:
            raise serializers.ValidationError({
                'feed-url': 'Invalid XML'
            })

        item = xml.find('channel/item')
        if not item:
            return []

        nsmap = xml.nsmap

        fields = []
        for field in item.findall('./'):
            fields.extend(_get_fields(field, nsmap))

        # Remove fields that are present more than once,
        # as we donot have support for list data yet.
        real_fields = []
        for field in fields:
            if fields.count(field) == 1:
                real_fields.append(field)
        return real_fields
