from rest_framework import viewsets

from .serializers import PageSerializer
from .models import Page


class PageViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Page.objects.all()
    serializer_class = PageSerializer
    lookup_field = 'page_id'
