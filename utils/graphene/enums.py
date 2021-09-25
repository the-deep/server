from typing import Union

import graphene
from django_enumfield import enum
from rest_framework import serializers
from django.db import models

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
    field: Union[serializers.ChoiceField, models.CharField, models.IntegerField, models.query_utils.DeferredAttribute],
):
    model_name = None
    field_name = None
    if type(field) == serializers.ChoiceField:
        model_name = field.parent.Meta.model.__name__
        field_name = field.field_name
    elif type(field) in [models.CharField, models.IntegerField]:
        model_name = field.model.__name__
        field_name = field.name
    elif type(field) == models.query_utils.DeferredAttribute:
        model_name = field.field.model.__name__
        field_name = field.field.name
    if model_name is None or field_name is None:
        raise Exception(f'{field=} | {type(field)=}: Both {model_name=} and {field_name=} should have a value')
    return f'{model_name}{to_camelcase(field_name)}'


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
        Here value shoould always be callable get_FOO_display
        """
        return value()

    serialize = coerce_string
    parse_value = coerce_string
    parse_literal = graphene.String.parse_literal
