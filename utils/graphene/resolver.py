from graphene.types.resolver import dict_or_attr_resolver, set_default_resolver
from django.db.models.fields.files import FieldFile as DjangoFieldFile


def custom_dict_or_attr_resolver(*args, **kwargs):
    value = dict_or_attr_resolver(*args, **kwargs)
    # NOTE: Custom check for DjangoFieldFile
    if isinstance(value, DjangoFieldFile):
        # Empty DjangoFieldFile are not handled as None by graphene resolver.
        # Returning None instead of empty DjangoFieldFile
        if value:
            return value
        return None
    return value


set_default_resolver(custom_dict_or_attr_resolver)
