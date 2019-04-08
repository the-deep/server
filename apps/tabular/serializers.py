import time
from django.db import transaction
from rest_framework import serializers
from drf_dynamic_fields import DynamicFieldsMixin

from deep.serializers import (
    NestedCreateMixin,
    NestedUpdateMixin,
)

from deep.serializers import RemoveNullFieldsMixin
from user_resource.serializers import UserResourceSerializer

from geo.serializers import SimpleRegionSerializer, Region, AdminLevel

from entry.models import Entry

from .models import Book, Sheet, Field, Geodata
from .tasks import tabular_generate_column_image


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


class FieldSerializer(
        RemoveNullFieldsMixin,
        DynamicFieldsMixin,
        serializers.ModelSerializer
):
    geodata = serializers.SerializerMethodField()

    class Meta:
        model = Field
        exclude = ('sheet', 'cache',)

    def get_geodata(self, obj):
        if obj.type == Field.GEO and hasattr(obj, 'geodata'):
            return GeodataSerializer(obj.geodata).data
        return None

    def update(self, instance, validated_data):
        validated_data['cache'] = {'status': Field.CACHE_PENDING, 'time': time.time()}
        instance = super().update(instance, validated_data)
        transaction.on_commit(
            lambda: tabular_generate_column_image.delay(instance.id)
        )
        return instance


class FieldMetaSerializer(FieldSerializer):
    geodata = None

    class Meta:
        model = Field
        exclude = ('sheet', 'data', 'cache',)


class FieldProcessedOnlySerializer(FieldSerializer):
    class Meta:
        model = Field
        exclude = ('data',)


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


class SheetMetaSerializer(SheetSerializer):
    fields = FieldMetaSerializer(many=True, source='field_set', required=False)


class SheetProcessedOnlySerializer(SheetSerializer):
    fields = FieldProcessedOnlySerializer(
        many=True, source='get_processed_fields', required=False,
    )


class BookSerializer(
        RemoveNullFieldsMixin,
        DynamicFieldsMixin,
        UserResourceSerializer
):
    sheets = SheetSerializer(many=True, source='sheet_set', required=False)
    entry_count = serializers.SerializerMethodField()

    class Meta:
        model = Book
        fields = '__all__'

    def get_entry_count(self, instance):
        return Entry.objects.filter(
            tabular_field__sheet__book=instance.id,
        ).count()


class BookMetaSerializer(BookSerializer):
    sheets = SheetMetaSerializer(many=True, source='sheet_set', required=False)


class BookProcessedOnlySerializer(BookSerializer):
    sheets = SheetProcessedOnlySerializer(
        many=True, source='sheet_set', required=False,
    )
    pending_fields = serializers.SerializerMethodField()

    def get_pending_fields(self, instance):
        return instance.get_pending_fields_id()
