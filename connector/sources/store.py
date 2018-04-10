from . import (
    rss_feed,
)
import random


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


def get_random_source():
    sources = get_sources()
    return random.choice(sources)[0]
