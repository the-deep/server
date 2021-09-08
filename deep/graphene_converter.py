from graphene.types.generic import GenericScalar

from graphene_django.compat import HStoreField, JSONField, PGJSONField
from graphene_django.converter import convert_django_field
from graphene_django_extras.converter import convert_django_field as extra_convert_django_field


# Only registering for query
# Mutation register is handled in utils/graphene/mutations.py
@extra_convert_django_field.register(HStoreField)
@extra_convert_django_field.register(JSONField)
@extra_convert_django_field.register(PGJSONField)
@convert_django_field.register(HStoreField)
@convert_django_field.register(JSONField)
@convert_django_field.register(PGJSONField)
def custom_convert_json_field_to_scalar(field, register=None):
    # https://github.com/graphql-python/graphene-django/issues/303#issuecomment-339939955
    return GenericScalar(description=field.help_text, required=not field.null)
