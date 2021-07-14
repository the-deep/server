import uuid

import factory
from factory.django import DjangoModelFactory
from django.core.files.base import ContentFile

from .models import File


class FileFactory(DjangoModelFactory):
    class Meta:
        model = File

    uuid = factory.LazyAttribute(lambda x: str(uuid.uuid4()))
    title = factory.Sequence(lambda n: f'file-{n}')
    file = factory.LazyAttribute(
        lambda _: ContentFile(
            factory.django.ImageField()._make_data(
                {'width': 1024, 'height': 768}
            ), 'example.jpg'
        )
    )
    # is_public = factory.Iterator([True, False])
    mime_type = factory.Faker('mime_type')
    metadata = factory.Dict({'md5_hash': 'random-hash'})

    @factory.post_generation
    def addresses(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            for project in extracted:
                self.projects.add(project)
