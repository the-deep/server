from collections import OrderedDict
from . import (
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


sources_list = [
    relief_web.ReliefWeb,
    atom_feed.AtomFeed,
    rss_feed.RssFeed,
    emm.EMM,
    acaps_briefing_notes.AcapsBriefingNotes,
    unhcr_portal.UNHCRPortal,
    pdna.PDNA,
    research_center.ResearchResourceCenter,
    wpf.WorldFoodProgramme,
    humanitarian_response.HumanitarianResponse,
]

assert len(set([source.key for source in sources_list])) == len(sources_list), 'Duplicate key found for connectors'

source_store = OrderedDict([
    (source.key, source)
    for source in sources_list
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
