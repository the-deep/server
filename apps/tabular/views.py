from django.conf import settings
from django.db import transaction
from rest_framework.decorators import action
from rest_framework import (
    viewsets,
    exceptions,
    response,
    permissions,
    views,
)

from entry.models import Entry

from .models import Book, Sheet, Field, Geodata
from .tasks import tabular_extract_book, tabular_extract_geo
from .serializers import (
    BookSerializer,
    BookMetaSerializer,
    BookProcessedOnlySerializer,
    SheetSerializer,
    FieldSerializer,
    GeodataSerializer,
)


class BookViewSet(viewsets.ModelViewSet):
    queryset = Book.objects.all()
    serializer_class = BookSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'list':
            return BookMetaSerializer
        return super().get_serializer_class()

    @action(
        detail=True,
        url_path='processed',
        serializer_class=BookProcessedOnlySerializer,
    )
    def get_processed_only(self, request, pk=None, version=None):
        instance = self.get_object()
        if instance.get_status():
            serializer = self.get_serializer(instance)
            return response.Response(serializer.data)
        return response.Response({
            'status': Field.CACHE_PENDING,
        })

    @action(
        detail=True,
        url_path='entry-count',
    )
    def get_entry_count(self, request, pk=None, version=None):
        instance = self.get_object()
        count = Entry.objects.filter(
            tabular_field__sheet__book=instance.id,
        ).count()
        return response.Response({
            'count': count,
        })


class SheetViewSet(viewsets.ModelViewSet):
    queryset = Sheet.objects.all()
    serializer_class = SheetSerializer
    permission_classes = [permissions.IsAuthenticated]


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
            return response.Response({'book_id': book.pk})

        if not settings.TESTING:
            transaction.on_commit(
                lambda: tabular_extract_book.delay(book.pk)
            )

        book.status = Book.PENDING
        book.save()
        return response.Response({'book_id': book.pk})


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
            return response.Response({'geodata_id': geodata.pk})

        if not settings.TESTING:
            transaction.on_commit(
                lambda: tabular_extract_geo.delay(geodata.pk)
            )

        geodata.status = geodata.PENDING
        geodata.save()
        return response.Response({'geodata_id': geodata.pk})
