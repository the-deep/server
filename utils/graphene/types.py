from collections import OrderedDict

import graphene

from django.db.models import QuerySet
from graphene import ObjectType, Field, Int
# we will use graphene_django registry over the one from graphene_django_extras
# since it adds information regarding nullability in the schema definition
from graphene_django.registry import get_global_registry
from graphene_django.utils import DJANGO_FILTER_INSTALLED, is_valid_django_model
from graphene_django_extras import DjangoListObjectType, DjangoObjectType
from graphene_django_extras.base_types import factory_type
from graphene_django_extras.types import DjangoObjectOptions

from utils.graphene.fields import CustomDjangoListField
from utils.graphene.options import CustomObjectTypeOptions


class ClientIdMixin(graphene.ObjectType):
    client_id = graphene.String()

    def resolve_client_id(root, info):
        return getattr(root, 'client_id', root.id)


class CustomListObjectType(ObjectType):
    class Meta:
        abstract = True

    @classmethod
    def __init_subclass_with_meta__(
        cls,
        base_type=None,
        results_field_name=None,
        filterset_class=None,
        **options,
    ):

        assert base_type is not None, (
            'Base Type of the ListField should be defined in the Meta.'
        )

        if not DJANGO_FILTER_INSTALLED and filterset_class:
            raise Exception("Can only set filterset_class if Django-Filter is installed")

        if not filterset_class:
            from django_filters import rest_framework as df
            filterset_class = df.FilterSet

        results_field_name = results_field_name or "results"

        result_container = CustomDjangoListField(base_type)

        _meta = CustomObjectTypeOptions(cls)
        _meta.base_type = base_type
        _meta.results_field_name = results_field_name
        _meta.filterset_class = filterset_class
        _meta.fields = OrderedDict(
            [
                (results_field_name, result_container),
                (
                    "count",
                    Field(
                        Int,
                        name="totalCount",
                        description="Total count of matches elements",
                    ),
                ),
                (
                    "page",
                    Field(
                        Int,
                        name="page",
                        description="Page Number",
                    ),
                ),
                (
                    "pageSize",
                    Field(
                        Int,
                        name="pageSize",
                        description="Page Size",
                    ),
                )
            ]
        )

        super(CustomListObjectType, cls).__init_subclass_with_meta__(
            _meta=_meta, **options
        )


class CustomDjangoListObjectType(DjangoListObjectType):
    """
    Updates `DjangoListObjectType` to add page related fields into type definition
    """
    class Meta:
        abstract = True

    @classmethod
    def __init_subclass_with_meta__(
        cls,
        model=None,
        registry=None,
        results_field_name=None,
        pagination=None,
        only_fields=(),
        exclude_fields=(),
        filter_fields=None,
        queryset=None,
        filterset_class=None,
        **options,
    ):

        assert is_valid_django_model(model), (
            'You need to pass a valid Django Model in {}.Meta, received "{}".'
        ).format(cls.__name__, model)

        assert pagination is None, (
            'Pagination should be applied on the ListField enclosing {0} rather than its `{0}.Meta`.'
        ).format(cls.__name__)

        if not DJANGO_FILTER_INSTALLED and filter_fields:
            raise Exception("Can only set filter_fields if Django-Filter is installed")

        assert isinstance(queryset, QuerySet) or queryset is None, (
            "The attribute queryset in {} needs to be an instance of "
            'Django model queryset, received "{}".'
        ).format(cls.__name__, queryset)

        results_field_name = results_field_name or "results"

        baseType = get_global_registry().get_type_for_model(model)

        if not baseType:
            factory_kwargs = {
                "model": model,
                "only_fields": only_fields,
                "exclude_fields": exclude_fields,
                "filter_fields": filter_fields,
                "filterset_class": filterset_class,
                "pagination": pagination,
                "queryset": queryset,
                "registry": registry,
                "skip_registry": False,
            }
            baseType = factory_type("output", DjangoObjectType, **factory_kwargs)

        filter_fields = filter_fields or baseType._meta.filter_fields

        result_container = CustomDjangoListField(baseType)

        _meta = DjangoObjectOptions(cls)
        _meta.model = model
        _meta.queryset = queryset
        _meta.baseType = baseType
        _meta.results_field_name = results_field_name
        _meta.filter_fields = filter_fields
        _meta.exclude_fields = exclude_fields
        _meta.only_fields = only_fields
        _meta.filterset_class = filterset_class
        _meta.fields = OrderedDict(
            [
                (results_field_name, result_container),
                (
                    "count",
                    Field(
                        Int,
                        name="totalCount",
                        description="Total count of matches elements",
                    ),
                ),
                (
                    "page",
                    Field(
                        Int,
                        name="page",
                        description="Page Number",
                    ),
                ),
                (
                    "pageSize",
                    Field(
                        Int,
                        name="pageSize",
                        description="Page Size",
                    ),
                )
            ]
        )

        super(DjangoListObjectType, cls).__init_subclass_with_meta__(
            _meta=_meta, **options
        )
