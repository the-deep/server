import time

from django.db import transaction
from django.core.management.base import BaseCommand

from deep_explore.tasks import (
    update_deep_explore_entries_count_by_geo_aggreagate,
    generate_public_deep_explore_snapshot,
)
from geo.models import GeoArea


class ShowRunTime():
    def __init__(self, command: BaseCommand, func_name):
        self.func_name = func_name
        self.command = command

    def __enter__(self):
        self.start_time = time.time()
        return self

    def __exit__(self, *_):
        self.command.stdout.write(
            self.command.style.SUCCESS(
                f"{self.func_name} Runtime: {time.time() - self.start_time} seconds"
            )
        )


class Command(BaseCommand):
    def handle(self, **_):
        start_time = time.time()

        # Calculate centroid for geo_areas if not already.
        with ShowRunTime(self, 'GeoCentroid Update'):
            with transaction.atomic():
                GeoArea.sync_centroid()

        # Update explore data
        with ShowRunTime(self, 'Geo Entries Aggregate Update'):
            update_deep_explore_entries_count_by_geo_aggreagate()

        # Update public snapshots
        with ShowRunTime(self, 'DeepExplore Public Snapshot Update'):
            generate_public_deep_explore_snapshot()

        self.stdout.write(
            self.style.SUCCESS(
                f"Total Runtime: {time.time() - start_time} seconds"
            )
        )
