from rest_framework import serializers
from drf_dynamic_fields import DynamicFieldsMixin

from deep.serializers import (
    NestedCreateMixin,
    NestedUpdateMixin,
)

from deep.serializers import RemoveNullFieldsMixin
from user_resource.serializers import UserResourceSerializer

from geo.serializers import SimpleRegionSerializer, Region, AdminLevel

from .models import Book, Sheet, Field, Geodata


class GeodataSerializer(RemoveNullFieldsMixin, serializers.ModelSerializer):
    regions = serializers.SerializerMethodField()
    admin_levels = serializers.SerializerMethodField()

    class Meta:
        model = Geodata
        exclude = ('field',)

    def get_regions(self, geodata):
        if not geodata.data:
            return []
        area_ids = [d['selected_id'] for d in geodata.data]
        regions = Region.objects.filter(
            adminlevel__geoarea__id__in=area_ids
        ).distinct()
        return SimpleRegionSerializer(regions, many=True).data

    def get_admin_levels(self, geodata):
        if not geodata.data:
            return []
        area_ids = [d['selected_id'] for d in geodata.data]
        admin_levels = AdminLevel.objects.filter(
            geoarea__id__in=area_ids
        ).distinct()
        return admin_levels.values_list('id', flat=True)


class FieldSerializer(RemoveNullFieldsMixin, serializers.ModelSerializer):
    geodata = serializers.SerializerMethodField()

    class Meta:
        model = Field
        exclude = ('sheet',)

    def get_geodata(self, obj):
        if obj.type == Field.GEO and hasattr(obj, 'geodata'):
            return GeodataSerializer(obj.geodata).data
        return None


class SheetSerializer(
        RemoveNullFieldsMixin,
        NestedCreateMixin,
        NestedUpdateMixin,
        DynamicFieldsMixin,
        serializers.ModelSerializer
):
    fields = FieldSerializer(many=True, source='field_set', required=False)

    class Meta:
        model = Sheet
        exclude = ('book',)


class BookSerializer(
        RemoveNullFieldsMixin,
        DynamicFieldsMixin,
        UserResourceSerializer
):
    sheets = SheetSerializer(many=True, source='sheet_set', required=False)

    class Meta:
        model = Book
        fields = '__all__'
