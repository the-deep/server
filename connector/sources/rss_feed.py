from lxml import etree
import requests

from lead.models import Lead
from .base import Source


class DefaultElement:
    text = ''


default_element = DefaultElement()


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
            'key': 'website',
            'field_type': 'string',
            'title': 'Website',
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

    dynamic_fields = [2, 3, 4, 5]

    def fetch(self, params, page=None, limit=None):
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
        website = params.get('website')

        for item in items:
            def get_field(field):
                return ((field and item.find(field)) or default_element).text
            title = get_field(title_field)
            date = get_field(date_field)
            source = get_field(source_field)
            url = get_field(url_field)

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

        return results, len(results)

    def query_options(self, params):
        fields = self.query_fields(params)
        for field in self.dynamic_fields:
            self.options[field]['options'] = fields
        return self.options

    def query_fields(self, params):
        if not params or not params.get('feed-url'):
            return []

        r = requests.get(params['feed-url'])
        xml = etree.fromstring(r.content)
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
                'value': replace_ns(tag),
            })

        return fields
