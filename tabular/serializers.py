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
    fields = FieldSerializer(many=True, source='field_set', required=False)

    class Meta:
        model = Sheet
        exclude = ('book',)


class BookSerializer(DynamicFieldsMixin, UserResourceSerializer):
    sheets = SheetSerializer(many=True, source='sheet_set', required=False)

    class Meta:
        model = Book
        fields = '__all__'

    def save(self, *args, **kwargs):
        book = super().save(*args, **kwargs)
        if book.file_type in Book.META_REQUIRED_FILE_TYPES:
            if not settings.TESTING:
                transaction.on_commit(
                    lambda: tabular_meta_extract_book.delay(book.id)
                )
            book.status = Book.PENDING
            book.save()
        return book
