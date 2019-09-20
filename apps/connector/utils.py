from django.core.cache import cache
from django.conf import settings

from utils.common import replace_ns


def ConnectorWrapper(ConnectorClass):
    class WrappedClass(ConnectorClass):
        """
        This wraps the basic connector class and provides functionalities like
        profiling on fetch and caching on get_content
        """
        def get_leads(self, *args, **kwargs):
            try:
                ret = super().get_leads(*args, **kwargs)
            except Exception:
                raise Exception(
                    "Parsing Connector Source data for {} failed. Maybe the source HTML structure has changed".format(self.title)  # noqa
                )
            else:
                return ret

        def get_content(self, url, params):
            """
            This will get the cached content if present else fetch
            from respective source
            """
            url_params = f'{url}:{str(params)}'
            cache_key = f'connector_{hash(url_params)}'

            data = cache.get(cache_key)

            if not data:
                data = super().get_content(url, params)
                cache.set(cache_key, data, settings.CONNECTOR_CACHE_AGE)
                return data

            return data

    return WrappedClass


def get_rss_fields(item, nsmap, parent_tag=None):
    tag = '{}/{}'.format(parent_tag, item.tag) if parent_tag else item.tag
    childs = item.getchildren()
    fields = []
    if len(childs) > 0:
        children_fields = []
        for child in childs:
            children_fields.extend(get_rss_fields(child, nsmap, tag))
        fields.extend(children_fields)
    else:
        fields.append({
            'key': tag,
            'label': replace_ns(nsmap, tag),
        })
    return fields
