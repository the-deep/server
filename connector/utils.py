def handle_connector_parse_error(ConnectorClass):
    class NewClass(ConnectorClass):
        def fetch(self, *args, **kwargs):
            try:
                ret = super().fetch(*args, **kwargs)
            except Exception:
                raise Exception(
                    "Parsing Connector Source data for {} failed. Maybe the source HTML structure has changed".format(self.title)  # noqa
                )
            else:
                return ret
    return NewClass
