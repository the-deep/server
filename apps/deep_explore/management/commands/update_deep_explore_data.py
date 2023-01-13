import time

from django.core.management.base import BaseCommand

from deep_explore.tasks import update_deep_explore_entries_count_by_geo_aggreagate
from geo.models import GeoArea


class Command(BaseCommand):
    def handle(self, **_):
        start_time = time.time()
        update_deep_explore_entries_count_by_geo_aggreagate()

        # Calculate centroid for geo_areas if not already.
        geo_area_start_time = time.time()
        GeoArea.sync_centroid()
        self.stdout.write(
            self.style.SUCCESS(
                f"GeoCentroid Update Runtime: {time.time() - geo_area_start_time} seconds"
            )
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"Successfull. Runtime: {time.time() - start_time} seconds"
            )
        )
