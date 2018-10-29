from django.conf import settings
from django.db import transaction
from rest_framework import serializers
from drf_dynamic_fields import DynamicFieldsMixin

from deep.serializers import (
    NestedCreateMixin,
    NestedUpdateMixin,
)

from .tasks import tabular_meta_extract_book
from user_resource.serializers import UserResourceSerializer
from .models import Book, Sheet, Field, Geodata


class GeodataSerializer(serializers.ModelSerializer):
    class Meta:
        model = Geodata
        exclude = ('field',)


class FieldSerializer(serializers.ModelSerializer):
    geodata = serializers.SerializerMethodField()

    class Meta:
        model = Field
        exclude = ('sheet',)

    def get_geodata(self, obj):
        if obj.type == Field.GEO and hasattr(obj, 'geodata'):
            return GeodataSerializer(obj.geodata).data


class SheetSerializer(
        NestedCreateMixin,
        NestedUpdateMixin,
        DynamicFieldsMixin,
        serializers.ModelSerializer
):
    fields = FieldSerializer(many=True, source='field_set', required=False)

    class Meta:
        model = Sheet
        exclude = ('book',)


class BookSerializer(DynamicFieldsMixin, UserResourceSerializer):
    sheets = SheetSerializer(many=True, source='sheet_set', required=False)

    class Meta:
        model = Book
        fields = '__all__'

    def create(self, validated_data):
        book = super().create(validated_data)
        if book.file_type in Book.META_REQUIRED_FILE_TYPES:
            if not settings.TESTING:
                transaction.on_commit(
                    lambda: tabular_meta_extract_book.delay(book.id)
                )
            book.meta_status = Book.PENDING
            book.save()
        return book
