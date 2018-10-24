from rest_framework import serializers

from .models import Book, Sheet, Field


class FieldSerializer(serializers.ModelSerializer):
    class Meta:
        model = Field
        exclude = ('sheet',)


class SheetSerializer(serializers.ModelSerializer):
    fields = FieldSerializer(many=True, source='field_set')

    class Meta:
        model = Sheet
        exclude = ('book',)


class BookSerializer(serializers.ModelSerializer):
    sheets = SheetSerializer(many=True, source='sheet_set')

    class Meta:
        model = Book
        fields = '__all__'
