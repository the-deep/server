from . import (
    rss_feed,
)


source_store = {
    'rss-feed': rss_feed.RssFeed,
}

sources = None


def get_sources():
    global sources
    if sources:
        return sources

    sources = []
    for key, source in source_store.items():
        sources.append((key, source.title))
    sources = tuple(sources)
    return sources
