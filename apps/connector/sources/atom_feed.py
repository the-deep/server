import time
import feedparser
from rest_framework import serializers

from lead.models import Lead

from .rss_feed import RssFeed


def _get_field_value(item, field, default=None):
    if item:
        return item.get(field, default)
    return default


class AtomFeed(RssFeed):
    title = 'Atom Feed'
    key = 'atom-feed'

    def fetch(self, params, offset=None, limit=None):
        results = []
        if not params or not params.get('feed-url'):
            return results, 0

        feed_url = params['feed-url']
        feed = feedparser.parse(feed_url)
        items = feed.entries

        for item in items:
            data = {
                'source_type': Lead.RSS,
                **{
                    lead_field: _get_field_value(item, params.get(param_key))
                    for lead_field, param_key in self.option_lead_field_map.items()
                },
            }
            results.append(data)

        return results

    def query_fields(self, params):
        if not params or not params.get('feed-url'):
            return []

        feed_url = params['feed-url']
        feed = feedparser.parse(feed_url)
        items = feed.entries

        if feed.get('bozo_exception'):
            raise serializers.ValidationError({
                'feed-url': 'Could not fetch/parse atom feed'
            })

        if not items:
            return []

        skip_types = [list, feedparser.FeedParserDict, tuple, time.struct_time]
        fields = {}
        for item in items:
            for key, value in item.items():
                if value is None or key in fields:
                    pass
                elif value.__class__ in skip_types:
                    fields[key] = {}  # Ignore this fields
                else:
                    fields[key] = {
                        'key': key,
                        'label': key.replace('_', ' ').title(),
                    }

        return [option for option in fields.values() if option]
