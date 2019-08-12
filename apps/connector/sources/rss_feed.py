from urllib.parse import urlparse
from rest_framework import serializers
from lxml import etree
import requests
import copy

from utils.common import DEFAULT_HEADERS
from lead.models import Lead
from .base import Source

DEFAULT_ITEM_XPATH = 'channel/item'
ITEM_XPATH = {
    'feedly.com': '{http://www.w3.org/2005/Atom}entry',
}


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

    def get_item_xpath(self, url):
        super().__init__()
        return ITEM_XPATH.get(urlparse(url).netloc, DEFAULT_ITEM_XPATH)

    def fetch(self, params, offset=None, limit=None):
        results = []
        if not params or not params.get('feed-url'):
            return results, 0

        feed_url = params['feed-url']
        r = requests.get(params['feed-url'])
        xml = etree.fromstring(r.content)
        items = xml.findall(self.get_item_xpath(feed_url))

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
                return '' if element is None else element.text or element.get('href')
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

    def query_fields(self, params):
        if not params or not params.get('feed-url'):
            return []

        feed_url = params['feed-url']
        try:
            r = requests.get(feed_url, headers=DEFAULT_HEADERS)
            xml = etree.fromstring(r.content)
        except requests.exceptions.RequestException:
            raise serializers.ValidationError({
                'feed-url': 'Could not fetch rss feed'
            })
        except etree.XMLSyntaxError:
            raise serializers.ValidationError({
                'feed-url': 'Invalid XML'
            })

        item = xml.find(self.get_item_xpath(feed_url))
        if not item:
            return []

        nsmap = xml.nsmap

        def replace_ns(tag):
            for k, v in nsmap.items():
                k = k or ''
                tag = tag.replace('{{{}}}'.format(v), '{}:'.format(k))
            return tag

        def get_fields(item, parent_tag=None):
            tag = '{}/{}'.format(parent_tag, item.tag) if parent_tag else item.tag
            childs = item.getchildren()
            fields = []
            if len(childs) > 0:
                children_fields = []
                for child in childs:
                    children_fields.extend(get_fields(child, tag))
                fields.extend(children_fields)
            else:
                fields.append({
                    'key': tag,
                    'label': replace_ns(tag),
                })
            return fields

        fields = []
        for field in item.findall('./'):
            fields.extend(get_fields(field))

        # Remove fields that are present more than once,
        # as we donot have support for list data yet.
        real_fields = []
        for field in fields:
            if fields.count(field) == 1:
                real_fields.append(field)
        return real_fields
