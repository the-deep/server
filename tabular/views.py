from django.conf import settings
from django.db import transaction
from rest_framework import (
    viewsets,
    exceptions,
    response,
    permissions,
    views,
)

from .models import Book, Sheet, Field
from .tasks import tabular_extract_book
from .serializers import (
    BookSerializer, SheetSerializer, FieldSerializer
)


class BookViewSet(viewsets.ModelViewSet):
    queryset = Book.objects.all()
    serializer_class = BookSerializer
    permission_classes = [permissions.IsAuthenticated]


class SheetViewSet(viewsets.ModelViewSet):
    queryset = Sheet.objects.all()
    serializer_class = SheetSerializer
    permission_classes = [permissions.IsAuthenticated]


class FieldViewSet(viewsets.ModelViewSet):
    queryset = Field.objects.all()
    serializer_class = FieldSerializer
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
            return response.Response({'book_id': book.id})

        if not settings.TESTING:
            transaction.on_commit(
                lambda: tabular_extract_book.delay(book.id)
            )

        book.status = Book.PENDING
        book.save()
        return response.Response({'book_id': book.id})
