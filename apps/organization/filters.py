import django_filters

from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.db.models.functions import Length
from django.db import models

from utils.graphene.filters import MultipleInputFilter, IDFilter

from lead.models import Lead
from project.models import Project
from .models import Organization
from .enums import OrganizationOrderingEnum


class IsFromReliefWeb(admin.SimpleListFilter):
    YES = 'yes'
    NO = 'no'

    # Human-readable title which will be displayed in the
    # right admin sidebar just above the filter options.
    title = _('Is from Relief Web')

    # Parameter for the filter that will be used in the URL query.
    parameter_name = 'is_from_relief_web'

    def lookups(self, request, model_admin):
        return (
            (self.YES, 'Yes'),
            (self.NO, 'No'),
        )

    def queryset(self, request, queryset):
        if self.value() == self.YES:
            return queryset.filter(relief_web_id__isnull=False)
        if self.value() == self.NO:
            return queryset.filter(relief_web_id__isnull=True)
        else:
            return queryset.all()


class OrganizationFilterSet(django_filters.FilterSet):
    search = django_filters.CharFilter(method='search_filter')
    used_in_project = IDFilter(method='filter_used_in_project')
    ordering = MultipleInputFilter(
        OrganizationOrderingEnum,
        method='ordering_filter',
    )

    class Meta:
        model = Organization
        fields = ['id', 'verified']

    def search_filter(self, qs, _, value):
        if value:
            return qs.filter(
                models.Q(title__icontains=value) |
                models.Q(short_name__icontains=value) |
                models.Q(long_name__icontains=value) |
                models.Q(related_childs__title__icontains=value) |
                models.Q(related_childs__short_name__icontains=value) |
                models.Q(related_childs__long_name__icontains=value)
            ).distinct()
        return qs

    def filter_used_in_project(self, qs, _, value):
        if value:
            user = getattr(self.request, 'user', None)
            if user is None:
                return qs
            project = Project.get_for_gq(user, only_member=True).filter(id=value).first()
            if project is None:
                return qs
            # Only using lead for now.
            lead_organizations_queryset = Lead.objects.filter(project=project)
            return qs.filter(
                # Publishers
                models.Q(id__in=lead_organizations_queryset.values('source')) |
                # Authors
                models.Q(id__in=lead_organizations_queryset.values('authors__id')) |
                # Project stakeholders
                models.Q(id__in=project.organizations.values('id'))
            )
        return qs

    def ordering_filter(self, qs, _, value):
        if value:
            if (
                OrganizationOrderingEnum.ASC_TITLE_LENGTH.value in value or
                OrganizationOrderingEnum.DESC_TITLE_LENGTH.value in value
            ):
                qs = qs.annotate(**{
                    OrganizationOrderingEnum.ASC_TITLE_LENGTH.value: Length('title'),
                })
            return qs.order_by(*value)
        return qs

    @property
    def qs(self):
        qs = super().qs
        if 'ordering' not in self.data:
            # Default is Title Length
            qs = self.ordering_filter(
                qs,
                None,
                # As the length is same, using id as secondary.
                [OrganizationOrderingEnum.ASC_TITLE_LENGTH.value, OrganizationOrderingEnum.ASC_ID.value],
            )
        return qs
