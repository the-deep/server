from urllib.parse import urljoin
import reversion
from entry.models import Entry
from entry.utils import validate_image_for_entry


class CustomRequest:
    def __init__(self, user, root_url):
        self.root_url = root_url
        self.user = user

    def build_absolute_uri(self, path):
        return urljoin(self.root_url, path)


def migrate_entry(entry, root_url):
    image = entry.image
    if not image:
        return

    new_image = validate_image_for_entry(
        image,
        project=entry.lead.project,
        request=CustomRequest(entry.created_by, root_url),
    )

    if new_image == image:
        return

    Entry.objects.filter(
        id=entry.id
    ).update(
        image=new_image
    )


def migrate(*args):
    root_url = args[0]
    with reversion.create_revision():
        for entry in Entry.objects.all():
            migrate_entry(entry, root_url)
