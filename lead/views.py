from rest_framework import viewsets, permissions, filters
from rest_framework.parsers import MultiPartParser, FormParser
import django_filters

from deep.permissions import ModifyPermission
from user_resource.filters import UserResourceFilterSet

from lead.models import Lead
from lead.serializers import LeadSerializer


class LeadFilterSet(UserResourceFilterSet):
    """
    Lead filter set

    Exclude the attachment field and set the published_on field
    to support range of date.
    """
    published_on = django_filters.DateFromToRangeFilter()

    class Meta:
        model = Lead
        fields = ('__all__')
        exclude = ['attachment']


class LeadViewSet(viewsets.ModelViewSet):
    """
    Lead View
    """
    queryset = Lead.objects.all()
    serializer_class = LeadSerializer
    parser_classes = (MultiPartParser, FormParser,)
    permission_classes = [permissions.IsAuthenticated,
                          ModifyPermission]
    filter_backends = (django_filters.rest_framework.DjangoFilterBackend,
                       filters.SearchFilter, filters.OrderingFilter)
    filter_class = LeadFilterSet
    search_fields = ('title', 'source', 'text', 'url', 'website',)
    # ordering_fields = omitted to allow ordering by all read-only fields

    def get_queryset(self):
        return Lead.get_for(self.request.user)
