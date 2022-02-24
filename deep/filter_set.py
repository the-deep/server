import django_filters
from django import forms
from django.db import models


class DjangoFilterCSVWidget(django_filters.widgets.CSVWidget):
    def value_from_datadict(self, data, files, name):
        value = forms.Widget.value_from_datadict(self, data, files, name)

        if value is not None:
            if value == '':  # parse empty value as an empty list
                return []
            # if value is already list(by POST)
            elif type(value) is list:
                return value
            return [x.strip() for x in value.strip().split(',') if x.strip()]
        return None


class OrderEnumMixin():
    def ordering_filter(self, qs, _, value):
        for ordering in value:
            if ordering.startswith('-'):
                qs = qs.order_by(models.F(ordering).desc(nulls_last=True))
            else:
                qs = qs.order_by(models.F(ordering).asc(nulls_last=True))
        return qs
