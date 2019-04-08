from rest_framework import serializers
from lxml import etree
import requests
import copy

from utils.common import DEFAULT_HEADERS, parse_number
from lead.models import Lead
from .base import Source


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
            'title': 'Website',
            'options': [],
        },
        {
            'key': 'title-field',
            'field_type': 'select',
            'title': 'Title field',
            'options': [],
        },
        {
            'key': 'date-field',
            'field_type': 'select',
            'title': 'Published on field',
            'options': [],
        },
        {
            'key': 'source-field',
            'field_type': 'select',
            'title': 'Source field',
            'options': [],
        },
        {
            'key': 'url-field',
            'field_type': 'select',
            'title': 'URL field',
            'options': [],
        },
    ]

    dynamic_fields = [1, 2, 3, 4, 5]

    def fetch(self, params, offset=None, limit=None):
        results = []
        if not params or not params.get('feed-url'):
            return results, 0

        r = requests.get(params['feed-url'])
        xml = etree.fromstring(r.content)
        items = xml.findall('channel/item')

        title_field = params.get('title-field')
        date_field = params.get('date-field')
        source_field = params.get('source-field')
        url_field = params.get('url-field')
        website_field = params.get('website-field')

        for item in items:
            def get_field(field):
                if not field:
                    return ''
                element = item.find(field)
                return '' if element is None else element.text
            title = get_field(title_field)
            date = get_field(date_field)
            source = get_field(source_field)
            url = get_field(url_field)
            website = get_field(website_field)

            data = Lead(
                # FIXME: use proper key
                id=url,
                title=title,
                published_on=date,
                source=source,
                url=url,
                website=website,
                source_type=Lead.RSS,
            )
            results.append(data)

        return results, len(items)

    def query_options(self, params):
        fields = self.query_fields(params)
        options = copy.deepcopy(self.options)
        for field in self.dynamic_fields:
            options[field]['options'] = fields
        return options

    def query_fields(self, params, limit=None, offset=None):
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

        def replace_ns(tag):
            for k, v in nsmap.items():
                tag = tag.replace('{{{}}}'.format(v), '{}:'.format(k))
            return tag

        fields = []
        for child in item.findall('./'):
            tag = child.tag
            fields.append({
                'key': tag,
                'label': replace_ns(tag),
            })

        # Remove fields that are present more than once,
        # as we donot have support for list data yet.
        real_fields = []
        for field in fields:
            if fields.count(field) == 1:
                real_fields.append(field)

        if offset is None or offset < 0:
            offset = 1
        if not limit or limit < 0:
            limit = Source.DEFAULT_PER_PAGE
        return real_fields[offset:offset + limit]
