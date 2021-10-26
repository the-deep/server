from graphene.types.generic import GenericScalar

from graphene_django.compat import HStoreField, JSONField, PGJSONField
from graphene_django.converter import convert_django_field
from graphene_django_extras.converter import convert_django_field as extra_convert_django_field

# For Geo Fields
from django.contrib.gis.db import models as gis_models
from utils.graphene import geo_scalars


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


# For Geo Fields
GIS_FIELD_SCALAR = {
    "PointField": geo_scalars.PointScalar,
    "LineStringField": geo_scalars.LineStringScalar,
    "PolygonField": geo_scalars.PolygonScalar,
    "MultiPolygonField": geo_scalars.MultiPolygonScalar,
    "GeometryField": geo_scalars.GISScalar
}


@convert_django_field.register(gis_models.GeometryField)
@convert_django_field.register(gis_models.MultiPolygonField)
@convert_django_field.register(gis_models.PolygonField)
@convert_django_field.register(gis_models.LineStringField)
@convert_django_field.register(gis_models.PointField)
def gis_converter(field, registry=None):
    class_name = field.__class__.__name__
    return GIS_FIELD_SCALAR[class_name](
        required=not field.null, description=field.help_text
    )
