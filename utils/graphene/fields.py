import inspect
from functools import partial
from collections import OrderedDict
from typing import Type, Optional

from django.db.models import QuerySet
import graphene
from graphene.types.structures import Structure
from graphene.utils.str_converters import to_snake_case
from graphene_django.filter.utils import get_filtering_args_from_filterset
from graphene_django.utils import maybe_queryset, is_valid_django_model
from graphene_django.registry import get_global_registry
from graphene_django_extras import DjangoFilterPaginateListField
from graphene_django_extras.base_types import DjangoListObjectBase
from graphene_django_extras.fields import DjangoListField
from graphene_django_extras.filters.filter import get_filterset_class
from graphene_django_extras.paginations.pagination import BaseDjangoGraphqlPagination
from graphene_django_extras.settings import graphql_api_settings
from graphene_django_extras.utils import get_extra_filters
from graphene_django.rest_framework.serializer_converter import get_graphene_type_from_serializer_field
from rest_framework import serializers

from utils.graphene.pagination import OrderingOnlyArgumentPagination, NoOrderingPageGraphqlPagination


class CustomDjangoListObjectBase(DjangoListObjectBase):
    def __init__(self, results, count, page, pageSize, results_field_name="results"):
        self.results = results
        self.count = count
        self.results_field_name = results_field_name
        self.page = page
        self.pageSize = pageSize

    def to_dict(self):
        return {
            self.results_field_name: [e.to_dict() for e in self.results],
            "count": self.count,
            "page": self.page,
            "pageSize": self.pageSize
        }


class CustomDjangoListField(DjangoListField):
    """
    Removes the compulsion of using `get_queryset` in the DjangoListField
    """
    @staticmethod
    def list_resolver(
        django_object_type, resolver, root, info, **args
    ):
        queryset = maybe_queryset(resolver(root, info, **args))
        if queryset is None:
            queryset = QuerySet.none()  # FIXME: This will throw error

        if isinstance(queryset, QuerySet):
            if hasattr(django_object_type, 'get_queryset'):
                # Pass queryset to the DjangoObjectType get_queryset method
                queryset = maybe_queryset(django_object_type.get_queryset(queryset, info))
        return queryset

    def get_resolver(self, parent_resolver):
        _type = self.type
        if isinstance(_type, graphene.NonNull):
            _type = _type.of_type
        object_type = _type.of_type.of_type
        return partial(
            self.list_resolver,
            object_type,
            parent_resolver,
        )


class CustomPaginatedListObjectField(DjangoFilterPaginateListField):
    def __init__(
        self,
        _type,
        pagination=None,
        extra_filter_meta=None,
        filterset_class=None,
        *args,
        **kwargs,
    ):

        kwargs.setdefault("args", {})

        filterset_class = filterset_class or _type._meta.filterset_class
        self.filterset_class = get_filterset_class(filterset_class)
        self.filtering_args = get_filtering_args_from_non_model_filterset(
            self.filterset_class
        )
        kwargs["args"].update(self.filtering_args)

        pagination = pagination or OrderingOnlyArgumentPagination()

        if pagination is not None:
            assert isinstance(pagination, BaseDjangoGraphqlPagination), (
                'You need to pass a valid DjangoGraphqlPagination in DjangoFilterPaginateListField, received "{}".'
            ).format(pagination)

            pagination_kwargs = pagination.to_graphql_fields()

            self.pagination = pagination
            kwargs.update(**pagination_kwargs)

        self.accessor = kwargs.pop('accessor', None)
        super(DjangoFilterPaginateListField, self).__init__(
            _type, *args, **kwargs
        )

    def list_resolver(
            self, filterset_class, filtering_args, root, info, **kwargs
    ):

        filter_kwargs = {k: v for k, v in kwargs.items() if k in filtering_args}
        qs = getattr(root, self.accessor)
        if hasattr(qs, 'all'):
            qs = qs.all()
        qs = filterset_class(data=filter_kwargs, queryset=qs, request=info.context).qs
        count = qs.count()

        if getattr(self, "pagination", None):
            ordering = kwargs.pop(self.pagination.ordering_param, None) or self.pagination.ordering
            ordering = ','.join([to_snake_case(each) for each in ordering.strip(',').replace(' ', '').split(',')])
            'pageSize' in kwargs and kwargs['pageSize'] is None and kwargs.pop('pageSize')
            kwargs[self.pagination.ordering_param] = ordering
            qs = self.pagination.paginate_queryset(qs, **kwargs)

        return CustomDjangoListObjectBase(
            count=count,
            results=maybe_queryset(qs),
            results_field_name=self.type._meta.results_field_name,
            page=kwargs.get('page', 1) if hasattr(self.pagination, 'page') else None,
            pageSize=kwargs.get(  # TODO: Need to add cutoff to send max page size instead of requested
                'pageSize',
                graphql_api_settings.DEFAULT_PAGE_SIZE
            ) if hasattr(self.pagination, 'page') else None
        )

    def get_resolver(self, parent_resolver):
        current_type = self.type
        while isinstance(current_type, Structure):
            current_type = current_type.of_type
        return partial(
            self.list_resolver,
            self.filterset_class,
            self.filtering_args,
        )


class DjangoPaginatedListObjectField(DjangoFilterPaginateListField):
    def __init__(
        self,
        _type,
        pagination=None,
        fields=None,
        extra_filter_meta: Optional[dict] = None,
        filterset_class=None,
        *args,
        **kwargs,
    ):
        '''
        If pagination is None, then we will only allow Ordering fields.
            - The page size will respect the settings.
            - Client will not be able to add pagination params
        '''
        _fields = _type._meta.filter_fields
        _model = _type._meta.model

        self.fields = fields or _fields
        meta = dict(model=_model, fields=self.fields)
        if extra_filter_meta:
            meta.update(extra_filter_meta)

        filterset_class = filterset_class or _type._meta.filterset_class
        self.filterset_class = get_filterset_class(filterset_class, **meta)
        self.filtering_args = get_filtering_args_from_filterset(
            self.filterset_class, _type
        )
        kwargs.setdefault("args", {})
        kwargs["args"].update(self.filtering_args)

        pagination = pagination or OrderingOnlyArgumentPagination()

        if pagination is not None:
            assert isinstance(pagination, BaseDjangoGraphqlPagination), (
                'You need to pass a valid DjangoGraphqlPagination in DjangoFilterPaginateListField, received "{}".'
            ).format(pagination)

            pagination_kwargs = pagination.to_graphql_fields()

            self.pagination = pagination
            kwargs.update(**pagination_kwargs)

        if not kwargs.get("description", None):
            kwargs["description"] = "{} list".format(_type._meta.model.__name__)

        # accessor will be used with m2m or reverse_fk fields
        self.accessor = kwargs.pop('accessor', None)
        super(DjangoFilterPaginateListField, self).__init__(
            _type, *args, **kwargs
        )

    def list_resolver(
            self, manager, filterset_class, filtering_args, root, info, **kwargs
    ):
        filter_kwargs = {k: v for k, v in kwargs.items() if k in filtering_args}
        if self.accessor:
            qs = getattr(root, self.accessor)
            if hasattr(qs, 'all'):
                qs = qs.all()
            qs = filterset_class(data=filter_kwargs, queryset=qs, request=info.context).qs
        else:
            qs = self.get_queryset(manager, root, info, **kwargs)
            qs = filterset_class(data=filter_kwargs, queryset=qs, request=info.context).qs
            if root and is_valid_django_model(root._meta.model):
                extra_filters = get_extra_filters(root, manager.model)
                qs = qs.filter(**extra_filters)
        # TODO: Duplicate count (self.pagination.paginate_queryset also calls count)
        count = qs.count()

        if getattr(self, "pagination", None):
            ordering = kwargs.pop(self.pagination.ordering_param, None) or self.pagination.ordering
            if isinstance(self.pagination, NoOrderingPageGraphqlPagination):
                # This is handled in filterset
                kwargs[self.pagination.ordering_param] = None
            else:
                ordering = ','.join([to_snake_case(each) for each in ordering.strip(',').replace(' ', '').split(',')])
                kwargs[self.pagination.ordering_param] = ordering
            'pageSize' in kwargs and kwargs['pageSize'] is None and kwargs.pop('pageSize')
            qs = self.pagination.paginate_queryset(qs, **kwargs)

        return CustomDjangoListObjectBase(
            count=count,
            results=maybe_queryset(qs),
            results_field_name=self.type._meta.results_field_name,
            page=kwargs.get('page', 1) if hasattr(self.pagination, 'page_query_param') else None,
            pageSize=kwargs.get(  # TODO: Need to add cutoff to send max page size instead of requested
                'pageSize',
                graphql_api_settings.DEFAULT_PAGE_SIZE
            ) if hasattr(self.pagination, 'page_size_query_param') else None
        )


def get_filtering_args_from_non_model_filterset(filterset_class):
    from graphene_django.forms.converter import convert_form_field

    args = {}
    for name, filter_field in filterset_class.declared_filters.items():
        form_field = filter_field.field
        field_type = convert_form_field(form_field).Argument()
        field_type.description = filter_field.label
        args[name] = field_type
    return args


def generate_serializer_field_class(inner_type, serializer_field, non_null=False):
    new_serializer_field = type(
        "{}SerializerField".format(inner_type.__name__),
        (serializer_field,),
        {},
    )
    get_graphene_type_from_serializer_field.register(new_serializer_field)(
        lambda _: graphene.NonNull(inner_type) if non_null else inner_type
    )
    return new_serializer_field


# Only use this for single object type with direct scaler access.
def generate_object_field_from_input_type(input_type, skip_fields=[]):
    new_fields_map = {}
    for field_key, field in input_type._meta.fields.items():
        if field_key in skip_fields:
            continue
        _type = field.type
        if inspect.isclass(_type) and (
            issubclass(_type, graphene.Scalar) or
            issubclass(_type, graphene.Enum)
        ):
            new_fields_map[field_key] = graphene.Field(_type)
        else:
            new_fields_map[field_key] = _type
    return new_fields_map


# use this for input type with direct scaler fields only.
def generate_simple_object_type_from_input_type(input_type):
    new_fields_map = generate_object_field_from_input_type(input_type)
    return type(input_type._meta.name.replace('Input', ''), (graphene.ObjectType,), new_fields_map)


def compare_input_output_type_fields(input_type, output_type):
    if len(output_type._meta.fields) != len(input_type._meta.fields):
        for field in input_type._meta.fields.keys():
            if field not in output_type._meta.fields.keys():
                print('---> [Entry] Missing: ', field)
        raise Exception('Conversion failed')


def convert_serializer_field(field, convert_choices_to_enum=True, force_optional=False):
    """
    Converts a django rest frameworks field to a graphql field
    and marks the field as required if we are creating an type
    and the field itself is required
    """

    if isinstance(field, serializers.ChoiceField) and not convert_choices_to_enum:
        graphql_type = graphene.String
    # elif isinstance(field, serializers.FileField):
    #     graphql_type = Upload
    else:
        graphql_type = get_graphene_type_from_serializer_field(field)

    args = []
    kwargs = {
        "description": field.help_text,
        "required": field.required and not force_optional
    }

    # if it is a tuple or a list it means that we are returning
    # the graphql type and the child type
    if isinstance(graphql_type, (list, tuple)):
        kwargs["of_type"] = graphql_type[1]
        graphql_type = graphql_type[0]

    if isinstance(field, serializers.ModelSerializer):
        global_registry = get_global_registry()
        field_model = field.Meta.model
        args = [global_registry.get_type_for_model(field_model)]
    elif isinstance(field, serializers.Serializer):
        args = [convert_serializer_to_type(field.__class__)]
    elif isinstance(field, serializers.ListSerializer):
        field = field.child
        if isinstance(field, serializers.ModelSerializer):
            del kwargs["of_type"]
            global_registry = get_global_registry()
            field_model = field.Meta.model
            args = [global_registry.get_type_for_model(field_model)]
        elif isinstance(field, serializers.Serializer):
            kwargs["of_type"] = graphene.NonNull(convert_serializer_to_type(field.__class__))
    return graphql_type(*args, **kwargs)


def convert_serializer_to_type(serializer_class):
    """
    graphene_django.rest_framework.serializer_converter.convert_serializer_to_type
    """
    cached_type = convert_serializer_to_type.cache.get(
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
    ref_name = f'{serializer_name}Type'

    base_classes = (graphene.ObjectType,)

    ret_type = type(
        ref_name,
        base_classes,
        items,
    )
    convert_serializer_to_type.cache[serializer_class.__name__] = ret_type
    return ret_type


convert_serializer_to_type.cache = {}


def fields_for_serializer(
    serializer,
    only_fields,
    exclude_fields,
    convert_choices_to_enum=True,
    partial=False,
):
    """
    NOTE: Same as the original definition. Needs overriding to
    handle relative import of convert_serializer_field
    """
    fields = OrderedDict()
    for name, field in serializer.fields.items():
        is_not_in_only = only_fields and name not in only_fields
        is_excluded = name in exclude_fields
        if is_not_in_only or is_excluded:
            continue
        fields[name] = convert_serializer_field(
            field,
            convert_choices_to_enum=convert_choices_to_enum,
            force_optional=partial,
        )
    return fields


def generate_type_for_serializer(
    name: str,
    serializer_class,
    partial=False,
    update_cache=False,
) -> Type[graphene.InputObjectType]:
    # NOTE: Custom converter are defined in mutation which needs to be set first.
    from utils.graphene import mutation  # noqa:F401

    data_members = fields_for_serializer(
        serializer_class(),
        only_fields=[],
        exclude_fields=[],
        partial=partial,
    )
    _type = type(name, (graphene.ObjectType,), data_members)
    if update_cache:
        if name in convert_serializer_to_type.cache:
            raise Exception(f'<{name}> : <{serializer_class.__name__}> Alreay exists')
        convert_serializer_to_type.cache[serializer_class.__name__] = _type
    return _type
