from django.contrib.auth.models import User
from django.db import models
from rest_framework import viewsets, permissions, filters
import django_filters

from deep.permissions import ModifyPermission
from user_resource.filters import UserResourceFilterSet

from project.models import Project
from lead.models import Lead
from lead.serializers import LeadSerializer


class LeadFilterSet(UserResourceFilterSet):
    """
    Lead filter set

    Exclude the attachment field and set the published_on field
    to support range of date.
    Also make most fields filerable by multiple values using
    'in' lookup expressions and CSVWidget.
    """
    published_on = django_filters.DateFromToRangeFilter()
    project = django_filters.ModelMultipleChoiceFilter(
        queryset=Project.objects.all(),
        lookup_expr='in',
        widget=django_filters.widgets.CSVWidget,
    )
    confidentiality = django_filters.MultipleChoiceFilter(
        choices=Lead.CONFIDENTIALITIES,
        lookup_expr='in',
        widget=django_filters.widgets.CSVWidget,
    )
    status = django_filters.MultipleChoiceFilter(
        choices=Lead.STATUSES,
        lookup_expr='in',
        widget=django_filters.widgets.CSVWidget,
    )
    assignee = django_filters.ModelMultipleChoiceFilter(
        queryset=User.objects.all(),
        lookup_expr='in',
        widget=django_filters.widgets.CSVWidget,
    )

    class Meta:
        model = Lead
        fields = ('__all__')
        exclude = ['attachment']
        filter_overrides = {
            models.CharField: {
                'filter_class': django_filters.CharFilter,
                'extra': lambda f: {
                    'lookup_expr': 'icontains',
                },
            },
        }


class LeadViewSet(viewsets.ModelViewSet):
    """
    Lead View
    """
    queryset = Lead.objects.all()
    serializer_class = LeadSerializer
    permission_classes = [permissions.IsAuthenticated,
                          ModifyPermission]
    filter_backends = (django_filters.rest_framework.DjangoFilterBackend,
                       filters.SearchFilter, filters.OrderingFilter)
    filter_class = LeadFilterSet
    search_fields = ('title', 'source', 'text', 'url', 'website')
    # ordering_fields = omitted to allow ordering by all read-only fields

    def get_queryset(self):
        return Lead.get_for(self.request.user)
