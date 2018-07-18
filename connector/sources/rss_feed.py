from .base import Source
import feedparser

from lead.models import Lead


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
            'title': 'Website'
        },
        {
            'key': 'title-field',
            'field_type': 'string',
            'title': 'Title field'
        },
        {
            'key': 'date-field',
            'field_type': 'string',
            'title': 'Published on field'
        },
        {
            'key': 'source-field',
            'field_type': 'string',
            'title': 'Source field'
        },
        {
            'key': 'url-field',
            'field_type': 'string',
            'title': 'URL field'
        },
    ]

    def fetch(self, params, offset=None, limit=None):
        results = []
        if not params or not params.get('feed-url'):
            return results, 0

        feed = feedparser.parse(params['feed-url'])

        title_field = params.get('title-field')
        date_field = params.get('date-field')
        source_field = params.get('source-field')
        url_field = params.get('url-field')
        website = params.get('website')

        for entry in feed.entries:
            title = title_field and entry.get(title_field)
            date = date_field and entry.get(date_field)
            source = source_field and entry.get(source_field)
            url = url_field and entry.get(url_field)

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

    def query_fields(self, params):
        if not params or not params.get('feed-url'):
            return []

        feed = feedparser.parse(params['feed-url'])
        entries = feed.entries
        if len(entries) == 0:
            return []
        return list(entries[0].keys())
