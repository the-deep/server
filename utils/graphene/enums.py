from typing import Union

import graphene
from django_enumfield import enum
from rest_framework import serializers
from django.db import models
from django.contrib.postgres.fields import ArrayField

from utils.common import to_camelcase


def enum_description(v: enum.Enum) -> Union[str, None]:
    try:
        return str(v.label)
    except AttributeError:
        return None


def convert_enum_to_graphene_enum(enum, name=None, description=enum_description, deprecation_reason=None):
    description = description or enum.__doc__
    name = name or enum.__name__
    meta_dict = {
        "enum": enum,
        "description": description,
        "deprecation_reason": deprecation_reason,
    }
    meta_class = type("Meta", (object,), meta_dict)
    return type(name, (graphene.Enum,), {"Meta": meta_class})


def get_enum_name_from_django_field(
    field: Union[
        None,
        serializers.ChoiceField,
        models.CharField,
        models.IntegerField,
        models.SmallIntegerField,
        ArrayField,
        models.query_utils.DeferredAttribute,
    ],
    field_name=None,
    model_name=None,
    serializer_name=None,
):
    def _have_model(_field):
        if hasattr(_field, 'model') or hasattr(getattr(_field, 'Meta', None), 'model'):
            return True

    def _get_serializer_name(_field):
        if hasattr(_field, 'parent'):
            return type(_field.parent).__name__

    if field_name is None and model_name is None:
        if type(field) == serializers.ChoiceField:
            if type(field.parent) == serializers.ListField:
                if _have_model(field.parent.parent):
                    model_name = field.parent.parent.Meta.model.__name__
                serializer_name = _get_serializer_name(field.parent)
                field_name = field.parent.field_name
            else:
                if _have_model(field.parent):
                    model_name = field.parent.Meta.model.__name__
                serializer_name = _get_serializer_name(field)
                field_name = field.field_name
        elif type(field) == ArrayField:
            if _have_model(field):
                model_name = field.model.__name__
            serializer_name = _get_serializer_name(field)
            field_name = field.base_field.name
        elif type(field) in [models.CharField, models.SmallIntegerField, models.IntegerField]:
            if _have_model(field):
                model_name = field.model.__name__
            serializer_name = _get_serializer_name(field)
            field_name = field.name
        elif type(field) == models.query_utils.DeferredAttribute:
            if _have_model(field.field):
                model_name = field.field.model.__name__
            serializer_name = _get_serializer_name(field.field)
            field_name = field.field.name
    if field_name is None:
        raise Exception(f'{field=} should have a name')
    if model_name:
        return f'{model_name}{to_camelcase(field_name.title())}'
    if serializer_name:
        return f'{serializer_name}{to_camelcase(field_name.title())}'
    raise Exception(f'{serializer_name=} should have a value')


class EnumDescription(graphene.Scalar):
    # NOTE: This is for Field only. Not usable as InputField or Argument.
    # XXX: Maybe there is a better way then this.
    """
    The `EnumDescription` scalar type represents of Enum description data, represented as UTF-8
    character sequences. The String type is most often used by GraphQL to
    represent free-form human-readable text.
    """

    @staticmethod
    def coerce_string(value):
        """
        Here value should always be callable get_FOO_display
        """
        if callable(value):
            return value()
        return value

    serialize = coerce_string
    parse_value = coerce_string
    parse_literal = graphene.String.parse_literal
