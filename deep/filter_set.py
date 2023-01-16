import django_filters
import graphene
from typing import Tuple
from django import forms
from django.db import models

from graphene_django.filter.utils import get_filtering_args_from_filterset
from utils.graphene.fields import (
    generate_object_field_from_input_type,
    compare_input_output_type_fields,
)


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


def generate_type_for_filter_set(
    filter_set,
    used_node,
    type_name,
    input_type_name,
    custom_new_fields_map=None,
) -> Tuple[graphene.ObjectType, graphene.InputObjectType]:
    """
    For given filter_set eg: LeadGqlFilterSet
    It returns:
        - LeadGqlFilterSetInputType
        - LeadGqlFilterSetType
    """
    def generate_type_from_input_type(input_type):
        new_fields_map = generate_object_field_from_input_type(input_type)
        if custom_new_fields_map:
            new_fields_map.update(custom_new_fields_map)
        new_type = type(type_name, (graphene.ObjectType,), new_fields_map)
        compare_input_output_type_fields(input_type, new_type)
        return new_type

    input_type = type(
        input_type_name,
        (graphene.InputObjectType,),
        get_filtering_args_from_filterset(filter_set, used_node)
    )
    _type = generate_type_from_input_type(input_type)
    return _type, input_type
