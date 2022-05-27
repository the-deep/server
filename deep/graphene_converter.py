from aniso8601 import parse_date, parse_datetime, parse_time
import graphene
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


original_time_serialize = graphene.Time.serialize
original_date_serialize = graphene.Date.serialize
original_datetime_serialize = graphene.DateTime.serialize


# Add option to add string as well.
class CustomSerialize():
    @staticmethod
    def _parse(dt, parse_func):
        if isinstance(dt, str):
            return parse_func(dt)
        return dt

    @classmethod
    def time(cls, time) -> str:
        return original_time_serialize(
            cls._parse(time, parse_time)
        )

    @classmethod
    def date(cls, date) -> str:
        return original_date_serialize(
            cls._parse(date, parse_date)
        )

    @classmethod
    def datetime(cls, dt) -> str:
        return original_datetime_serialize(
            cls._parse(dt, parse_datetime)
        )


graphene.Time.serialize = CustomSerialize.time
graphene.Date.serialize = CustomSerialize.date
graphene.DateTime.serialize = CustomSerialize.datetime
