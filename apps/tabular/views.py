from django.conf import settings
from django.db import transaction
from entry.models import Entry
from rest_framework import exceptions, permissions, response, views, viewsets
from rest_framework.decorators import action

from .models import Book, Field, Geodata, Sheet
from .serializers import (
    BookMetaSerializer,
    BookProcessedOnlySerializer,
    BookSerializer,
    FieldProcessedOnlySerializer,
    FieldSerializer,
    GeodataSerializer,
    SheetMetaSerializer,
    SheetSerializer,
)
from .tasks import tabular_extract_book, tabular_extract_geo


class BookViewSet(viewsets.ModelViewSet):
    queryset = Book.objects.all()
    serializer_class = BookSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.action == "list":
            return BookMetaSerializer
        return super().get_serializer_class()

    @action(
        detail=True,
        url_path="processed",
        serializer_class=BookProcessedOnlySerializer,
    )
    def get_processed_only(self, request, pk=None, version=None):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return response.Response(serializer.data)

    @action(
        detail=True,
        url_path="fields",
        methods=["post"],
        serializer_class=FieldProcessedOnlySerializer,
    )
    def get_fields(self, request, pk=None, version=None):
        instance = self.get_object()
        fields = request.data.get("fields", [])
        pending_fields = instance.get_pending_fields_id()
        fields = instance.get_processed_fields(fields)
        serializer = self.get_serializer(fields, many=True)
        return response.Response(
            {
                "pending_fields": pending_fields,
                "fields": serializer.data,
            }
        )

    @action(
        detail=True,
        url_path="entry-count",
    )
    def get_entry_count(self, request, pk=None, version=None):
        instance = self.get_object()
        count = Entry.objects.filter(
            tabular_field__sheet__book=instance.id,
        ).count()
        return response.Response(
            {
                "count": count,
            }
        )

    @action(
        detail=True,
        url_path="sheets",
        methods=["patch"],
    )
    def update_sheets(self, request, pk=None, version=None):
        instance = self.get_object()
        sheets = request.data.get("sheets", [])
        sheet_maps = {x["id"]: x for x in sheets}

        sheet_objs = Sheet.objects.filter(book=instance, id__in=[x["id"] for x in sheets])
        for sheet in sheet_objs:
            serializer = SheetSerializer(
                sheet,
                data=sheet_maps[sheet.id],
                context={"request": request},
                partial=True,
            )
            serializer.is_valid()
            serializer.update(sheet, sheet_maps[sheet.id])

        return response.Response(
            BookMetaSerializer(instance, context={"request": request}).data,
        )


class SheetViewSet(viewsets.ModelViewSet):
    queryset = Sheet.objects.all()
    serializer_class = SheetSerializer
    permission_classes = [permissions.IsAuthenticated]

    @action(
        detail=True,
        url_path="fields",
        methods=["patch"],
    )
    def update_fields(self, request, pk=None, version=None):
        instance = self.get_object()
        fields = request.data.get("fields", [])
        field_maps = {x["id"]: x for x in fields}

        field_objs = Field.objects.filter(sheet=instance, id__in=[x["id"] for x in fields])

        for field in field_objs:
            serializer = FieldSerializer(
                field,
                data=field_maps[field.id],
                context={"request": request},
                partial=True,
            )
            serializer.is_valid()
            serializer.update(field, field_maps[field.id])

        return response.Response(
            SheetMetaSerializer(instance, context={"request": request}).data,
        )


class FieldViewSet(viewsets.ModelViewSet):
    queryset = Field.objects.all()
    serializer_class = FieldSerializer
    permission_classes = [permissions.IsAuthenticated]


class GeodataViewSet(viewsets.ModelViewSet):
    queryset = Geodata.objects.all()
    serializer_class = GeodataSerializer
    permission_classes = [permissions.IsAuthenticated]


class TabularExtractionTriggerView(views.APIView):
    """
    A trigger for extracting tabular data for book
    """

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, book_id, version=None):
        if not Book.objects.filter(id=book_id).exists():
            raise exceptions.NotFound()

        book = Book.objects.get(id=book_id)

        if book.status == Book.SUCCESS:
            return response.Response({"book_id": book.pk})

        if not settings.TESTING:
            transaction.on_commit(lambda: tabular_extract_book.delay(book.pk))

        book.status = Book.PENDING
        book.save()
        return response.Response({"book_id": book.pk})


class TabularGeoProcessTriggerView(views.APIView):
    """
    A trigger for processing geo data for given field
    """

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, field_id, version=None):
        if not Field.objects.filter(id=field_id).exists():
            raise exceptions.NotFound()

        field = Field.objects.get(pk=field_id)
        geodata = Geodata.objects.filter(field=field_id).first()
        if not geodata:
            geodata = Geodata.objects.create(field=field)

        if geodata.status == Geodata.SUCCESS:
            return response.Response({"geodata_id": geodata.pk})

        if not settings.TESTING:
            transaction.on_commit(lambda: tabular_extract_geo.delay(geodata.pk))

        geodata.status = geodata.PENDING
        geodata.save()
        return response.Response({"geodata_id": geodata.pk})
