from collections import OrderedDict

from django.db import models
from django.utils.encoding import force_text
from rest_framework import exceptions, serializers
from rest_framework.compat import uritemplate

from . import schema


def field_to_schema(field):
    title = force_text(field.label) if field.label else ''
    description = force_text(field.help_text) if field.help_text else ''

    if isinstance(field, (serializers.ListSerializer, serializers.ListField)):
        return schema.Array(
            items=field_to_schema(field.child),
            title=title,
            description=description
        )
    elif isinstance(field, serializers.Serializer):
        return schema.Object(
            properties=OrderedDict([
                (key, field_to_schema(value))
                for key, value
                in field.fields.items()
            ]),
            title=title,
            description=description
        )
    elif isinstance(field, serializers.ManyRelatedField):
        return schema.Array(
            items=field_to_schema(field.child_relation),
            title=title,
            description=description
        )
    elif isinstance(field, serializers.RelatedField):
        # TODO Check if stringrelatedfield or primarykeyrelatedfield
        #      or ...
        return schema.Integer(title=title, description=description)
    elif isinstance(field, serializers.MultipleChoiceField):
        return schema.Array(
            items=schema.Enum(enum=list(field.choices.keys())),
            title=title,
            description=description
        )
    elif isinstance(field, serializers.ChoiceField):
        return schema.Enum(
            enum=list(field.choices.keys()),
            title=title,
            description=description
        )
    elif isinstance(field, serializers.BooleanField):
        return schema.Boolean(title=title, description=description)
    elif isinstance(field, (serializers.DecimalField, serializers.FloatField)):
        return schema.Number(title=title, description=description)
    elif isinstance(field, serializers.IntegerField):
        return schema.Integer(title=title, description=description)

    if field.style.get('base_template') == 'textarea.html':
        return schema.String(
            title=title,
            description=description,
            format='textarea'
        )

    return schema.String(title=title, description=description)


def get_pk_description(model, model_field):
    if isinstance(model_field, models.AutoField):
        value_type = 'unique integer value'
    elif isinstance(model_field, models.UUIDField):
        value_type = 'UUID string'
    else:
        value_type = 'unique value'

    return 'A {value_type} identifying this {name}'.format(
        value_type=value_type,
        name=model._meta.verbose_name,
    )


class Field:
    def __init__(self,
                 name='',
                 location='',
                 required='',
                 schema=None):
        self.name = name
        self.location = location
        self.required = required
        self.schema = schema

    def __str__(self):
        return self.name

    def __repr__(self):
        return str(self)


class ViewSchema:
    def __init__(self, view, path, method):
        self.view = view

        self.path = path
        self.method = method

        self.request_fields = []
        self.response_fields = []

        self.get_path_fields()
        self.get_serializer_fields()

    def get_path_fields(self):
        view = self.view
        path = self.path

        model = getattr(getattr(view, 'queryset', None), 'model', None)

        for variable in uritemplate.variables(path):
            title = ''
            description = ''
            schema_cls = schema.String
            kwargs = {}

            if model is not None:
                try:
                    model_field = model._meta.get_field(variable)
                except:
                    model_field = None

                if model_field is not None:
                    if model_field.verbose_name:
                        title = force_text(model_field.verbose_name)

                    if model_field.help_text:
                        description = force_text(model_field.help_text)
                    elif model_field.primary_key:
                        description = get_pk_description(model, model_field)

                if hasattr(view, 'lookup_value_regex') and \
                        view.lookup_field == variable:
                    kwargs['pattern'] = view.lookup_value_regex
                elif isinstance(model_field, models.AutoField):
                    schema_cls = schema.Integer

                # Check other field types ? It's mostly string though

            field = Field(
                name=variable,
                location='path',
                required=True,
                schema=schema_cls(title=title, description=description,
                                  **kwargs)
            )
            self.request_fields.append(field)
            self.response_fields.append(field)

    def get_serializer_fields(self):
        view = self.view
        method = self.method

        if method not in ('PUT', 'PATCH', 'POST'):
            return

        if not hasattr(view, 'get_serializer'):
            return

        try:
            serializer = view.get_serializer()
        except exceptions.APIException:
            serializer = None
            # Note not generated for view.__class__.name, method, path

        if isinstance(serializer, serializers.ListSerializer):
            # self.request_fields.append([
            #     Field(
            #         name='data',
            #         location='body',
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
                name=field.field_name,
                location='form',
                required=required,
                schema=field_to_schema(field),
            )

            if not field.read_only:
                self.request_fields.append(out_field)
            if not field.write_only:
                self.response_fields.append(out_field)
