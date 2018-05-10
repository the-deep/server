from django.contrib import admin
from organization.models import (
    OrganizationType,
    Organization,
)


admin.site.register(OrganizationType)
admin.site.register(Organization)
