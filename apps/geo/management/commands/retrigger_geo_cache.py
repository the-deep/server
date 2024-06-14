import logging

from django.core.management.base import BaseCommand
from django.db import transaction
from geo.models import AdminLevel, Region

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Re-trigger cached data for all geo entities. For specific objects admin panel"

    def add_arguments(self, parser):
        parser.add_argument(
            "--region",
            action="store_true",
            help="Calculate all regions cache",
        )
        parser.add_argument(
            "--admin-level",
            action="store_true",
            help="Calculate all regions admin level cache",
        )

    def calculate(self, Model):
        success_ids = []
        qs = Model.objects.all()
        total = qs.count()
        for index, item in enumerate(qs.all(), start=1):
            try:
                self.stdout.write(f"({index}/{total}) [{item.pk}] {item.title}")
                with transaction.atomic():
                    item.calc_cache()
                success_ids.append(item.pk)
            except Exception:
                logger.error(f"{Model.__name__} Cache Calculation Failed!!", exc_info=True)
        self.stdout.write(self.style.SUCCESS(f"{success_ids=}"))

    def handle(self, *_, **options):
        calculate_regions = options["region"]
        calculate_admin_levels = options["admin_level"]

        if calculate_regions:
            self.calculate(Region)
        if calculate_admin_levels:
            self.calculate(AdminLevel)
