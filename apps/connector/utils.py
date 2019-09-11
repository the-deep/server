def handle_connector_parse_error(ConnectorClass):
    class Handler(ConnectorClass):
        def get_leads(self, *args, **kwargs):
            try:
                ret = super().get_leads(*args, **kwargs)
            except Exception:
                raise Exception(
                    "Parsing Connector Source data for {} failed. Maybe the source HTML structure has changed".format(self.title)  # noqa
                )
            else:
                return ret
    return Handler
