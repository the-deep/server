from .base import Source, SourceData
import feedparser


class RssFeed(Source):
    title = 'RSS Feed'
    key = 'rss-feed'
    options = {
        'feed-url': {'type': 'url', 'title': 'Feed URL'},
        'title-field': {'type': 'string', 'title': 'Title field'},
        'date-field': {'type': 'string', 'title': 'Published on field'},
        'source-field': {'type': 'string', 'title': 'Source field'},
        'url-field': {'type': 'string', 'title': 'URL field'},
    }

    def fetch(params, page=None, limit=None):
        feed = feedparser.parse(params['feed-url'])
        results = []

        for entry in feed.entries:
            title = entry[params['title-field']]
            date = entry[params['date-field']]
            source = entry[params['source-field']]
            url = entry[params['url-field']]
            data = SourceData(
                title=title,
                published_on=date,
                source=source,
                url=url,
            )

            results.append(data)

        return results
