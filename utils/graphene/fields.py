from functools import partial

from django.db.models import QuerySet
from graphene import NonNull
from graphene.types.structures import Structure
from graphene.utils.str_converters import to_snake_case
from graphene_django.filter.utils import get_filtering_args_from_filterset
from graphene_django.utils import maybe_queryset, is_valid_django_model
from graphene_django_extras import DjangoFilterPaginateListField
from graphene_django_extras.base_types import DjangoListObjectBase
from graphene_django_extras.fields import DjangoListField
from graphene_django_extras.filters.filter import get_filterset_class
from graphene_django_extras.paginations.pagination import BaseDjangoGraphqlPagination
from graphene_django_extras.settings import graphql_api_settings
from graphene_django_extras.utils import get_extra_filters

from utils.graphene.pagination import OrderingOnlyArgumentPagination


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
        if isinstance(_type, NonNull):
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
            self.pagination.ordering = ordering
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
        extra_filter_meta=None,
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
            qs = self.get_queryset(manager, info, **kwargs)
            qs = filterset_class(data=filter_kwargs, queryset=qs, request=info.context).qs
            if root and is_valid_django_model(root._meta.model):
                extra_filters = get_extra_filters(root, manager.model)
                qs = qs.filter(**extra_filters)
        count = qs.count()

        if getattr(self, "pagination", None):
            ordering = kwargs.pop(self.pagination.ordering_param, None) or self.pagination.ordering
            ordering = ','.join([to_snake_case(each) for each in ordering.strip(',').replace(' ', '').split(',')])
            self.pagination.ordering = ordering
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
