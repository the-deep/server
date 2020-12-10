import django_filters
from django import forms


class DjangoFilterCSVWidget(django_filters.widgets.CSVWidget):
    def value_from_datadict(self, data, files, name):
        value = forms.Widget.value_from_datadict(self, data, files, name)

        if value is not None:
            if value == '':  # parse empty value as an empty list
                return []
            # if value is already list(by POST)
            elif type(value) is list:
                return value
            return value.split(',')
        return None
