from collections import OrderedDict
from unified_connector.sources import (
    atom_feed,
    rss_feed,
    acaps_briefing_notes,
    unhcr_portal,
    relief_web,
    pdna,
    research_center,
    wpf,
    humanitarian_response,
    emm,
)
import random


source_store = OrderedDict([
    (atom_feed.AtomFeed.key, atom_feed.AtomFeed),
    ('rss-feed', rss_feed.RssFeed),
    ('emm', emm.EMM),
    ('acaps-briefing-notes', acaps_briefing_notes.AcapsBriefingNotes),
    ('unhcr-portal', unhcr_portal.UNHCRPortal),
    ('relief-web', relief_web.ReliefWeb),
    ('post-disaster-needs-assessment', pdna.PDNA),
    ('research-resource-center', research_center.ResearchResourceCenter),
    ('world-food-programme', wpf.WorldFoodProgramme),
    ('humanitarian-response', humanitarian_response.HumanitarianResponse),
])

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
