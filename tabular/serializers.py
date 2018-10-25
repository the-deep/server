from rest_framework import serializers
from drf_dynamic_fields import DynamicFieldsMixin

from deep.serializers import (
    NestedCreateMixin,
    NestedUpdateMixin,
)
from user_resource.serializers import UserResourceSerializer
from .models import Book, Sheet, Field


class FieldSerializer(serializers.ModelSerializer):
    class Meta:
        model = Field
        exclude = ('sheet',)


class SheetSerializer(
        NestedCreateMixin,
        NestedUpdateMixin,
        DynamicFieldsMixin,
        serializers.ModelSerializer
):
    fields = FieldSerializer(many=True, source='field_set')

    class Meta:
        model = Sheet
        exclude = ('book',)


class BookSerializer(DynamicFieldsMixin, UserResourceSerializer):
    sheets = SheetSerializer(many=True, source='sheet_set')

    class Meta:
        model = Book
        fields = '__all__'
