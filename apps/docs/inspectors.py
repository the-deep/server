from collections import OrderedDict

from django.test.client import RequestFactory
from django.db import models
from django.core.exceptions import FieldDoesNotExist
from rest_framework import exceptions, serializers
from rest_framework.compat import uritemplate

from deep.serializers import RecursiveSerializer
from user.models import User
from .utils import is_list_view, is_custom_action
from . import schema


def to_camel_case(snake_str):
    components = snake_str.split('_')
    return components[0] + "".join(x.title() for x in components[1:])


def format_field_name(field_name, required, camelcase):
    if camelcase:
        field_name = to_camel_case(field_name)
    if required:
        field_name += '*'
    return field_name


def field_to_schema(field, camelcase=True):
    # title = force_text(field.label) if field.label else ''
    # if camelcase:
    #     title = to_camel_case(title)
    # description = force_text(field.help_text) if field.help_text else ''

    if isinstance(field, RecursiveSerializer):
        return schema.Recursive()

    if isinstance(field, (serializers.ListSerializer, serializers.ListField)):
        return schema.Array(
            items=field_to_schema(field.child),
        )

    elif isinstance(field, serializers.Serializer):
        return schema.Object(
            properties=OrderedDict([
                (
                    format_field_name(value.field_name,
                                      value.required, camelcase),
                    field_to_schema(value)
                ) for value in field.fields.values()
            ]),
        )

    elif isinstance(field, serializers.ManyRelatedField):
        return schema.Array(
            items=field_to_schema(field.child_relation),
        )

    elif isinstance(field, serializers.RelatedField):
        # TODO Check if stringrelatedfield or primarykeyrelatedfield
        #      or ...
        return schema.Integer()

    elif isinstance(field, serializers.MultipleChoiceField):
        return schema.Array(
            items=schema.Enum(enum=list(field.choices.keys())),
        )
    elif isinstance(field, serializers.ChoiceField):
        return schema.Enum(
            enum=list(field.choices.keys()),
        )

    elif isinstance(field, serializers.BooleanField):
        return schema.Boolean()
    elif isinstance(field, (serializers.DecimalField, serializers.FloatField)):
        return schema.Number()
    elif isinstance(field, serializers.IntegerField):
        return schema.Integer()

    elif isinstance(field, serializers.JSONField):
        return schema.CustomJson()
    elif isinstance(field, serializers.DateField):
        return schema.Date()
    elif isinstance(field, serializers.TimeField):
        return schema.Time()
    elif isinstance(field, serializers.DateTimeField):
        return schema.DateTime()
    elif isinstance(field, serializers.URLField):
        return schema.URL()

    elif isinstance(field, (serializers.FileField, serializers.ImageField)):
        return schema.File()

    if field.style.get('base_template') == 'textarea.html':
        return schema.String(
            format='textarea'
        )

    return schema.String()


def get_pk_description(model, model_field):
    if isinstance(model_field, models.AutoField):
        value_type = 'unique integer value'
    elif isinstance(model_field, models.UUIDField):
        value_type = 'UUID string'
    else:
        value_type = 'unique value'

    return 'A {value_type} identifying this {title}'.format(
        value_type=value_type,
        title=model._meta.verbose_name,
    )


class Field:
    def __init__(self,
                 title='',
                 required=False,
                 schema=None):
        self.title = title
        self.required = required
        self.schema = schema

    def __str__(self):
        if self.required:
            return self.title + '*'
        return self.title

    def __repr__(self):
        return str(self)


class ViewSchema:
    def __init__(self, view, path, method):
        self.view = view

        self.path = path
        self.method = method

        self.request_fields = []
        self.response_fields = []
        self.path_fields = []

        self.get_path_fields()
        self.get_serializer_fields()

        self.handle_pagination()

    def get_path_fields(self):
        view = self.view
        path = self.path

        model = getattr(getattr(view, 'queryset', None), 'model', None)

        for variable in uritemplate.variables(path):
            schema_cls = schema.String
            kwargs = {}

            if model is not None:
                try:
                    model_field = model._meta.get_field(variable)
                except FieldDoesNotExist:
                    model_field = None

                # if model_field is not None:
                #     if model_field.verbose_name:
                #         title = force_text(model_field.verbose_name)

                #     if model_field.help_text:
                #         description = force_text(model_field.help_text)
                #     elif model_field.primary_key:
                #         description = get_pk_description(model, model_field)

                if hasattr(view, 'lookup_value_regex') and \
                        view.lookup_field == variable:
                    kwargs['pattern'] = view.lookup_value_regex
                if isinstance(model_field, models.AutoField):
                    schema_cls = schema.Integer

                # Check other field types ? It's mostly string though

            field = Field(
                title=variable,
                required=True,
                schema=schema_cls(**kwargs)
            )
            self.path_fields.append(field)

    def get_serializer_fields(self):
        view = self.view
        method = self.method

        if hasattr(view, 'action') and is_custom_action(view.action):
            action = getattr(view, view.action)
            if getattr(action, 'delete_view', False):
                return

        if method in ('DELETE',):
            return

        takes_request = method in ('PUT', 'PATCH', 'POST')

        if not hasattr(view, 'get_serializer'):
            return

        try:
            view.request = RequestFactory()
            view.request.user = User(username='test')
            serializer = view.get_serializer()
        except exceptions.APIException:
            serializer = None
            # Note not generated for view.__class__.name, method, path

        if isinstance(serializer, serializers.ListSerializer):
            # self.request_fields.append([
            #     Field(
            #         title='data',
            #         required=True,
            #         schema=schema.Array(),
            #     )
            # ])
            # TODO Figure out why this was used in the rest_framework's
            #      AutoSchema class
            return

        if not isinstance(serializer, serializers.Serializer):
            return

        for field in serializer.fields.values():
            if isinstance(field, serializers.HiddenField):
                continue

            required = field.required and method != 'PATCH'
            out_field = Field(
                title=to_camel_case(field.field_name),
                required=required,
                schema=field_to_schema(field),
            )

            if not field.read_only and takes_request:
                self.request_fields.append(out_field)
            if not field.write_only:
                self.response_fields.append(out_field)

    def handle_pagination(self):
        # TODO: Check if pagination is enabled and is of this format

        # For now assume, limit offset pagination

        if is_list_view(self.path, self.method, self.view):
            response_fields = []

            response_fields.append(Field(
                title='count',
                required=True,
                schema=schema.Integer(),
            ))

            response_fields.append(Field(
                title='next',
                required=False,
                schema=schema.URL(),
            ))

            response_fields.append(Field(
                title='previous',
                required=False,
                schema=schema.URL(),
            ))

            response_fields.append(Field(
                title='results',
                required=True,
                schema=schema.Array(
                    items=schema.Object(
                        properties=OrderedDict([
                            (str(field), field.schema) for field in
                            self.response_fields
                        ])
                    ),
                ),
            ))

            self.response_fields = response_fields
