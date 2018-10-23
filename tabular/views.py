from django.conf import settings
from django.db import transaction
from rest_framework import (
    viewsets,
    exceptions,
    response,
    permissions,
    views,
)

from gallery.models import File
from .models import Book
from .tasks import tabular_extract_from_file
from .serializers import BookSerializer


class BookViewSet(viewsets.ModelViewSet):
    queryset = Book.objects.all()
    serializer_class = BookSerializer
    permission_classes = [permissions.IsAuthenticated]


class TabularFileExtractionTriggerView(views.APIView):
    """
    A trigger for extracting tabular data from file
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, file_id, version=None):
        if not File.objects.filter(id=file_id).exists():
            raise exceptions.NotFound()

        if not File.objects.get(id=file_id).get_for(request.user):
            raise exceptions.PermissionDenied()

        file = File.objects.get(id=file_id)

        if Book.objects.filter(file=file).exists():
            raise exceptions.ValidationError(detail='Already Exists', code=409)

        book = Book.objects.create(
            title=file.title,
            file=file,
            file_type=request.data.get('file_type'),
            options=request.data.get('options'),
            created_by=request.user,
            modified_by=request.user,
        )
        book.save()

        if not settings.TESTING:
            transaction.on_commit(
                lambda: tabular_extract_from_file.delay(book.id)
            )

        return response.Response({
            'extraction_triggered': file_id,
            'book_id': book.id,
        })
