from urllib.parse import urljoin
import reversion
from entry.models import Entry
from entry.utils import base64_to_deep_image


class CustomRequest:
    def __init__(self, user, root_url):
        self.root_url = root_url
        self.user = user

    def build_absolute_uri(self, path):
        return urljoin(self.root_url, path)


def migrate_entry(entry, root_url):
    image = entry.image_raw
    if not image:
        return

    new_image = base64_to_deep_image(
        image,
        entry.lead,
        entry.created_by,
    )

    if new_image == image:
        return

    Entry.objects.filter(
        id=entry.id
    ).update(
        image=new_image
    )


def migrate(*args):
    print('This should be already migrated')
    return
    root_url = args[0]
    with reversion.create_revision():
        for entry in Entry.objects.all():
            migrate_entry(entry, root_url)
