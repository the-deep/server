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
            if isinstance(ordering, str):
                if ordering.startswith('-'):
                    _ordering = models.F(ordering[1:]).desc()
                else:
                    _ordering = models.F(ordering).asc()
                qs = qs.order_by(_ordering)
            else:
                _ordering = ordering
            _ordering.nulls_last = True
            qs = qs.order_by(_ordering)
        return qs


def get_dummy_request(**kwargs):
    return type(
        'DummyRequest', (object,),
        kwargs,
    )()
