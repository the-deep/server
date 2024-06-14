from django.contrib.gis.db.models.fields import BaseSpatialField
from django.contrib.gis.db.models.functions import GeoFuncMixin
from django.db.models import BooleanField, Func, Transform


class StrPos(Func):
    function = "POSITION"  # MySQL method

    def as_sqlite(self, compiler, connection):
        #  SQLite method
        return self.as_sql(compiler, connection, function="INSTR")

    def as_postgresql(self, compiler, connection):
        # PostgreSQL method
        return self.as_sql(compiler, connection, function="STRPOS")


@BaseSpatialField.register_lookup
class IsEmpty(GeoFuncMixin, Transform):
    # From https://github.com/django/django/commit/2a14b8df39b573124ea42dec0ce96147c8e767d4
    # Remove this after Upgrade to Django 4
    lookup_name = "isempty"
    output_field = BooleanField()
