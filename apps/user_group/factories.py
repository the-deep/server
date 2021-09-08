import factory
from factory import fuzzy
from factory.django import DjangoModelFactory

from .models import UserGroup


class UserGroupFactory(DjangoModelFactory):
    class Meta:
        model = UserGroup

    title = factory.Sequence(lambda n: f'Group-{n}')
    description = fuzzy.FuzzyText(length=15)
    display_picture = factory.SubFactory('gallery.factories.FileFactory')
    global_crisis_monitoring = factory.Faker('pybool')
    custom_project_fields = factory.Dict({'custom-field': 'custom-value'})

    @factory.post_generation
    def members(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            for member in extracted:
                self.members.add(member)
