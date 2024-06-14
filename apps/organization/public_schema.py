from graphene_django import DjangoObjectType

from utils.graphene.types import CustomDjangoListObjectType

from .filters import OrganizationFilterSet
from .models import Organization


class PublicOrganization(DjangoObjectType):
    class Meta:
        model = Organization
        skip_registry = True
        fields = ("id", "title")


class PublicOrganizationListObjectType(CustomDjangoListObjectType):
    class Meta:
        model = Organization
        base_type = PublicOrganization
        filterset_class = OrganizationFilterSet
