from datetime import datetime, date


class ExtractorMixin:
    """
    Mixin that implements get_date_str and serialized_data
    """
    # fields are accessed by get_{fielname}. If fieldname is to be reanamed, mention
    # it as 'source_field:rename_to'. For example: 'date_str:date' will have date_str value
    # in 'date' field of serialized_data

    fields = ['title', 'date_str:date', 'country', 'source', 'website', 'author']

    def get_date_str(self):
        parsed = self.get_date()
        if isinstance(parsed, (datetime, date)):
            return parsed
        return parsed

    def serialized_data(self):
        data = {}
        for fieldname in self.fields:
            if ':' in fieldname:
                source_field, rename_as = fieldname.split(':')[:2]
            else:
                source_field, rename_as = fieldname, fieldname
            getter = getattr(self, f'get_{source_field}')
            data[rename_as] = getter and getter()
        return data
