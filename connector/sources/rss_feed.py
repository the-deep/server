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

    def fetch(self, params, page=None, limit=None):
        feed = feedparser.parse(params['feed-url'])
        results = []

        for entry in feed.entries:
            title = entry[params['title-field']]
            date = entry[params['date-field']]
            source = entry[params['source-field']]
            url = entry[params['url-field']]
            data = Lead(
                title=title,
                published_on=date,
                source=source,
                url=url,
                website='reliefweb.int',
                source_type=Lead.RSS,
            )

            results.append(data)

        return results
