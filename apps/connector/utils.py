from utils.common import replace_ns, LogTime


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

        @LogTime(log_args=False)
        def get_content(self, url, params):
            return super().get_content(url, params)

        @LogTime(log_args=False)
        def fetch(self, *args, **kwargs):
            return super().fetch(*args, **kwargs)

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
