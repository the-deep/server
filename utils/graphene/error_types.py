from typing import List

import graphene
from graphene import ObjectType
from graphene.types.generic import GenericScalar
from graphene.utils.str_converters import to_snake_case
from graphene_django.utils.utils import _camelize_django_str

ARRAY_NON_MEMBER_ERRORS = 'nonMemberErrors'
CustomErrorType = GenericScalar


class ArrayNestedErrorType(ObjectType):
    key = graphene.String(required=True)
    messages = graphene.String(required=False)
    object_errors = graphene.List(graphene.NonNull(GenericScalar))

    def keys(self):
        return ['key', 'messages', 'objectErrors']

    def __getitem__(self, key):
        key = to_snake_case(key)
        if key in ('object_errors',) and getattr(self, key):
            return [dict(each) for each in getattr(self, key)]
        return getattr(self, key)


class _CustomErrorType(ObjectType):
    field = graphene.String(required=True)
    messages = graphene.String(required=False)
    object_errors = graphene.List(graphene.NonNull(GenericScalar))
    array_errors = graphene.List(graphene.NonNull(ArrayNestedErrorType))

    def keys(self):
        return ['field', 'messages', 'objectErrors', 'arrayErrors']

    def __getitem__(self, key):
        key = to_snake_case(key)
        if key in ('object_errors', 'array_errors') and getattr(self, key):
            return [dict(each) for each in getattr(self, key)]
        return getattr(self, key)


def serializer_error_to_error_types(errors: dict, initial_data: dict = None) -> List:
    initial_data = initial_data or dict()
    error_types = list()
    for field, value in errors.items():
        if isinstance(value, dict):
            error_types.append(_CustomErrorType(
                field=_camelize_django_str(field),
                object_errors=serializer_error_to_error_types(value)
            ))
        elif isinstance(value, list):
            if isinstance(value[0], str):
                if isinstance(initial_data.get(field), list):
                    # we have found an array input with top level error
                    error_types.append(_CustomErrorType(
                        field=_camelize_django_str(field),
                        array_errors=[ArrayNestedErrorType(
                            key=ARRAY_NON_MEMBER_ERRORS,
                            messages=''.join(str(msg) for msg in value)
                        )]
                    ))
                else:
                    error_types.append(_CustomErrorType(
                        field=_camelize_django_str(field),
                        messages=''.join(str(msg) for msg in value)
                    ))
            elif isinstance(value[0], dict):
                array_errors = []
                for pos, array_item in enumerate(value):
                    if not array_item:
                        # array item might not have error
                        continue
                    # fetch array.item.uuid from the initial data
                    key = initial_data[field][pos].get('uuid', f'NOT_FOUND_{pos}')
                    array_errors.append(ArrayNestedErrorType(
                        key=key,
                        object_errors=serializer_error_to_error_types(array_item, initial_data[field][pos])
                    ))
                error_types.append(_CustomErrorType(
                    field=_camelize_django_str(field),
                    array_errors=array_errors
                ))
        else:
            # fallback
            error_types.append(_CustomErrorType(
                field=_camelize_django_str(field),
                messages=' '.join(str(msg) for msg in value)
            ))
    return error_types


def mutation_is_not_valid(serializer) -> List[dict]:
    """
    Checks if serializer is valid, if not returns list of errorTypes
    """
    if not serializer.is_valid():
        errors = serializer_error_to_error_types(serializer.errors, serializer.initial_data)
        return [dict(each) for each in errors]
    return []
