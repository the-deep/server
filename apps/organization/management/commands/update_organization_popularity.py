from collections import defaultdict

from django.core.management.base import BaseCommand
from django.db import models
from lead.models import Lead
from organization.models import Organization

COUNT_THRESHOLD = 10


class Command(BaseCommand):
    """
    Update organization popularity using number of leads attached to that organization
    """

    def handle(self, *args, **kwargs):
        lead_qs = Lead.objects.filter(project__is_test=False)
        lead_author_qs = (
            lead_qs.filter(authors__isnull=False)
            .annotate(
                organization_id=models.functions.Coalesce(
                    models.F("authors__parent_id"),
                    models.F("authors__id"),
                )
            )
            .order_by()
            .values("organization_id")
            .annotate(count=models.Count("id"))
        )

        lead_source_qs = (
            lead_qs.filter(source__isnull=False)
            .annotate(
                organization_id=models.functions.Coalesce(
                    models.F("source__parent_id"),
                    models.F("source__id"),
                )
            )
            .order_by()
            .values("organization_id")
            .annotate(count=models.Count("id"))
        )

        organization_popularity_map = defaultdict(int)
        for qs in [
            lead_author_qs,
            lead_source_qs,
        ]:
            for org_id, count in qs.filter(count__gt=COUNT_THRESHOLD).values_list("organization_id", "count"):
                organization_popularity_map[org_id] += count

        Organization.objects.bulk_update(
            [
                Organization(
                    id=_id,
                    popularity=count,
                )
                for _id, count in organization_popularity_map.items()
            ],
            ["popularity"],
        )
