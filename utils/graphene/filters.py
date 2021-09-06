import django_filters
import graphene
from graphene.types.generic import GenericScalar
from graphene_django.forms.converter import convert_form_field

from deep.filter_set import DjangoFilterCSVWidget


class NumberInFilter(django_filters.BaseInFilter, django_filters.NumberFilter):
    pass


def _generate_filter_class(inner_type, filter_type=None):
    _filter_type = filter_type or django_filters.Filter
    form_field = type(
        "{}FormField".format(inner_type.__name__),
        (_filter_type.field_class,),
        {},
    )
    filter_class = type(
        "{}Filter".format(inner_type.__name__),
        (_filter_type,),
        {
            "field_class": form_field,
            "__doc__": (
                "{0}Filter is a small extension of a raw {1} "
                "that allows us to express graphql ({0}) arguments using FilterSets."
                "Note that the given values are passed directly into queryset filters."
            ).format(inner_type.__name__, _filter_type),
        },
    )
    convert_form_field.register(form_field)(
        lambda _: inner_type()
    )

    return filter_class


def _generate_list_filter_class(inner_type, filter_type=None, field_class=None):
    """
    Source: https://github.com/graphql-python/graphene-django/issues/190

    Returns a Filter class that will resolve into a List(`inner_type`) graphene
    type.

    This allows us to do things like use `__in` filters that accept graphene
    lists instead of a comma delimited value string that's interpolated into
    a list by django_filters.BaseCSVFilter (which is used to define
    django_filters.BaseInFilter)
    """

    _filter_type = filter_type or django_filters.Filter
    _field_class = field_class or _filter_type.field_class
    form_field = type(
        "List{}FormField".format(inner_type.__name__),
        (_field_class,),
        {},
    )
    filter_class = type(
        "{}ListFilter".format(inner_type.__name__),
        (_filter_type,),
        {
            "field_class": form_field,
            "__doc__": (
                "{0}ListFilter is a small extension of a raw {1} "
                "that allows us to express graphql List({0}) arguments using FilterSets."
                "Note that the given values are passed directly into queryset filters."
            ).format(inner_type.__name__, _filter_type),
        },
    )
    convert_form_field.register(form_field)(
        lambda _: graphene.List(graphene.NonNull(inner_type))
    )

    return filter_class


def _get_simple_input_filter(_type, **kwargs):
    return _generate_filter_class(_type)(**kwargs)


def _get_multiple_input_filter(_type, **kwargs):
    return _generate_list_filter_class(
        _type,
        filter_type=django_filters.MultipleChoiceFilter,
        # TODO: Hack, not sure why django_filters.MultipleChoiceFilter.field_class doesn't work
        field_class=django_filters.Filter.field_class,
    )(**kwargs)


def _get_id_list_filter(**kwargs):
    return _generate_filter_class(
        graphene.ID,
        filter_type=NumberInFilter,
    )(widget=DjangoFilterCSVWidget, **kwargs)


SimpleInputFilter = _get_simple_input_filter
MultipleInputFilter = _get_multiple_input_filter

# Generic Filters
IDListFilter = _get_id_list_filter
StringListFilter = _generate_list_filter_class(graphene.String)
GenericFilter = _generate_filter_class(GenericScalar)
