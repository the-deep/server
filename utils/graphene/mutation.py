from typing import Type, List
from collections import OrderedDict

from django.core.exceptions import PermissionDenied
import graphene
import graphene_django
from graphene.types.generic import GenericScalar
from graphene_django.registry import get_global_registry
from graphene_django.rest_framework.serializer_converter import (
    get_graphene_type_from_serializer_field,
)
from rest_framework import serializers

from utils.graphene.error_types import mutation_is_not_valid
# from utils.common import to_camelcase
# from deep.enums import ENUM_TO_GRAPHENE_ENUM_MAP
from deep.permissions import (
    ProjectPermissions as PP,
    AnalysisFrameworkPermissions as AfP,
)


@get_graphene_type_from_serializer_field.register(serializers.ListSerializer)
def convert_list_serializer_to_field(field):
    child_type = get_graphene_type_from_serializer_field(field.child)
    return (graphene.List, graphene.NonNull(child_type))


@get_graphene_type_from_serializer_field.register(serializers.ListField)
def convert_list_field_to_field(field):
    child_type = get_graphene_type_from_serializer_field(field.child)
    return (graphene.List, graphene.NonNull(child_type))


@get_graphene_type_from_serializer_field.register(serializers.ManyRelatedField)
def convert_serializer_field_to_many_related_id(field):
    return (graphene.List, graphene.NonNull(graphene.ID))


@get_graphene_type_from_serializer_field.register(serializers.PrimaryKeyRelatedField)
# @get_graphene_type_from_serializer_field.register(IntegerIDField)
def convert_serializer_field_to_id(field):
    return graphene.ID


@get_graphene_type_from_serializer_field.register(serializers.JSONField)
def convert_serializer_field_to_jsonstring(field):
    return GenericScalar

# TODO: https://github.com/graphql-python/graphene-django/blob/623d0f219ebeaf2b11de4d7f79d84da8508197c8/graphene_django/converter.py#L83-L94  # noqa: E501
# https://github.com/graphql-python/graphene-django/blob/623d0f219ebeaf2b11de4d7f79d84da8508197c8/graphene_django/rest_framework/serializer_converter.py#L155-L159  # noqa: E501
# @get_graphene_type_from_serializer_field.register(serializers.ChoiceField)
# def convert_serializer_field_to_enum(field):
#     return ENUM_TO_GRAPHENE_ENUM_MAP.get(name, graphene.String)


def convert_serializer_field(field, is_input=True, convert_choices_to_enum=True):
    """
    Converts a django rest frameworks field to a graphql field
    and marks the field as required if we are creating an input type
    and the field itself is required
    """

    if isinstance(field, serializers.ChoiceField) and not convert_choices_to_enum:
        graphql_type = graphene.String
    else:
        graphql_type = get_graphene_type_from_serializer_field(field)

    args = []
    kwargs = {"description": field.help_text, "required": is_input and field.required}

    # if it is a tuple or a list it means that we are returning
    # the graphql type and the child type
    if isinstance(graphql_type, (list, tuple)):
        kwargs["of_type"] = graphql_type[1]
        graphql_type = graphql_type[0]

    if isinstance(field, serializers.ModelSerializer):
        if is_input:
            graphql_type = convert_serializer_to_input_type(field.__class__)
        else:
            global_registry = get_global_registry()
            field_model = field.Meta.model
            args = [global_registry.get_type_for_model(field_model)]
    elif isinstance(field, serializers.ListSerializer):
        field = field.child
        if is_input:
            # All the serializer items within the list is considered non-nullable
            kwargs["of_type"] = graphene.NonNull(convert_serializer_to_input_type(field.__class__))
        else:
            del kwargs["of_type"]
            global_registry = get_global_registry()
            field_model = field.Meta.model
            args = [global_registry.get_type_for_model(field_model)]

    return graphql_type(*args, **kwargs)


def convert_serializer_to_input_type(serializer_class):
    """
    graphene_django.rest_framework.serializer_converter.convert_serializer_to_input_type
    """
    cached_type = convert_serializer_to_input_type.cache.get(
        serializer_class.__name__, None
    )
    if cached_type:
        return cached_type
    serializer = serializer_class()

    items = {
        name: convert_serializer_field(field)
        for name, field in serializer.fields.items()
    }
    # Alter naming
    serializer_name = serializer.__class__.__name__
    serializer_name = ''.join(''.join(serializer_name.split('ModelSerializer')).split('Serializer'))
    ref_name = f'{serializer_name}InputType'

    base_classes = (graphene.InputObjectType,)

    ret_type = type(
        ref_name,
        base_classes,
        items,
    )
    convert_serializer_to_input_type.cache[serializer_class.__name__] = ret_type
    return ret_type


convert_serializer_to_input_type.cache = {}


def fields_for_serializer(
    serializer,
    only_fields,
    exclude_fields,
    is_input=False,
    convert_choices_to_enum=True,
    lookup_field=None
):
    """
    NOTE: Same as the original definition. Needs overriding to
    handle relative import of convert_serializer_field
    """
    fields = OrderedDict()
    for name, field in serializer.fields.items():
        is_not_in_only = only_fields and name not in only_fields
        is_excluded = any(
            [
                name in exclude_fields,
                field.write_only and
                not is_input,  # don't show write_only fields in Query
                field.read_only and is_input \
                and lookup_field != name,  # don't show read_only fields in Input
            ]
        )

        if is_not_in_only or is_excluded:
            continue

        fields[name] = convert_serializer_field(
            field, is_input=is_input, convert_choices_to_enum=convert_choices_to_enum
        )
    return fields


def generate_input_type_for_serializer(
    name: str,
    serializer_class,
) -> Type[graphene.InputObjectType]:
    data_members = fields_for_serializer(
        serializer_class(),
        only_fields=[],
        exclude_fields=[],
        is_input=True
    )
    return type(name, (graphene.InputObjectType,), data_members)


# override the default implementation
graphene_django.rest_framework.serializer_converter.convert_serializer_field = convert_serializer_field
graphene_django.rest_framework.serializer_converter.convert_serializer_to_input_type = convert_serializer_to_input_type


class BaseGrapheneMutation(graphene.Mutation):
    # output fields
    errors = graphene.List(graphene.NonNull(GenericScalar))

    @classmethod
    def filter_queryset(cls, qs, info):
        # customize me in the mutation if required
        return qs

    # Graphene standard method
    @classmethod
    def get_queryset(cls, info):
        return cls.filter_queryset(cls.model._meta.default_manager.all(), info)

    @classmethod
    def get_object(cls, info, **kwargs):
        obj = cls.get_queryset(info).get(id=kwargs['id'])
        return obj

    # @classmethod
    # def check_permissions(cls, info, **kwargs):
    #     raise Exception('This needs to be implemented in inheritances class')

    @classmethod
    def _save_item(cls, item, info, **kwargs):
        id = kwargs.pop('id', None)
        if id:
            serializer = cls.serializer_class(
                instance=cls.get_object(info, id=id, **kwargs),
                data=item,
                context={'request': info.context},
                partial=True,
            )
        else:
            serializer = cls.serializer_class(
                data=item,
                context={'request': info.context}
            )
        errors = mutation_is_not_valid(serializer)
        if errors:
            return None, errors
        instance = serializer.save()
        return instance, None

    # Graphene standard method
    @classmethod
    def mutate(cls, root, info, **kwargs):
        cls.check_permissions(info, **kwargs)
        return cls.perform_mutate(root, info, **kwargs)


class GrapheneMutation(BaseGrapheneMutation):
    ok = graphene.Boolean()

    @classmethod
    def perform_mutate(cls, root, info, **kwargs):
        data = kwargs['data']
        instance, errors = cls._save_item(data, info, **kwargs)
        return cls(result=instance, errors=errors, ok=not errors)


class BulkGrapheneMutation(BaseGrapheneMutation):
    errors = graphene.List(graphene.List(graphene.NonNull(GenericScalar)))

    @classmethod
    def perform_mutate(cls, root, info, **kwargs):
        items = kwargs.get('items') or []
        delete_ids = kwargs.get('delete_ids')
        all_errors = []
        all_instances = []
        all_deleted_instances = []
        # Create/Update
        for item in items:
            id = item.get('id')
            instance, errors = cls._save_item(item, info, id=id, **kwargs)
            all_errors.append(errors)
            all_instances.append(instance)
        if delete_ids:
            # Delete (NOTE: define get_valid_delete_items when used)
            delete_items = cls.get_valid_delete_items(info, delete_ids)
            for item in delete_items:
                old_id = item.pk
                item.delete()
                # add old id so that client can use it if required
                item.pk = old_id
                all_deleted_instances.append(item)
            # cls.model.filter(pk__in=validated_delete_ids).delete()
        return cls(result=all_instances, errors=all_errors, deleted_result=all_deleted_instances)


class DeleteMutation(GrapheneMutation):
    ok = graphene.Boolean()

    @classmethod
    def perform_mutate(cls, root, info, **kwargs):
        instance = cls.get_object(info, **kwargs)
        old_id = instance.id
        instance.delete()
        # add old id so that client can use it if required
        instance.id = old_id
        return cls(result=instance, errors=None, ok=True)


class ProjectScopeMixin():
    permissions: List[str]

    @classmethod
    def check_permissions(cls, info, **_):
        for permission in cls.permissions:
            if not PP.check_permission(info, permission):
                raise PermissionDenied(PP.get_permission_message(permission))


class PsGrapheneMutation(ProjectScopeMixin, GrapheneMutation):
    pass


class PsBulkGrapheneMutation(ProjectScopeMixin, BulkGrapheneMutation):
    pass


class PsDeleteMutation(ProjectScopeMixin, DeleteMutation):
    pass


class AfScopeMixin():
    permissions: List[str]

    @classmethod
    def check_permissions(cls, info, **_):
        for permission in cls.permissions:
            if not AfP.check_permission(info, permission):
                raise PermissionDenied(AfP.get_permission_message(permission))


class AfGrapheneMutation(AfScopeMixin, GrapheneMutation):
    pass


class AfBulkGrapheneMutation(AfScopeMixin, BulkGrapheneMutation):
    pass
