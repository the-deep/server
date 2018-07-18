from . import (
    rss_feed,
    acaps_briefing_notes,
    unhcr_portal,
    relief_web,
)
import random


source_store = {
    'rss-feed': rss_feed.RssFeed,
    'acaps-briefing-notes': acaps_briefing_notes.AcapsBriefingNotes,
    'unhcr-portal': unhcr_portal.UNHCRPortal,
    'relief-web': relief_web.ReliefWeb,
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
