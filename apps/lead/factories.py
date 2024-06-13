import factory
import datetime
from factory import fuzzy
from factory.django import DjangoModelFactory

from django.core.files.base import ContentFile

from project.factories import ProjectFactory
from gallery.factories import FileFactory
from .models import (
    Lead,
    EMMEntity,
    LeadGroup,
    LeadEMMTrigger,
    LeadPreview,
    LeadPreviewAttachment,
    UserSavedLeadFilter,
)


DEFAULT_START_DATE = datetime.date(year=2017, month=1, day=1)


class LeadFactory(DjangoModelFactory):
    title = factory.Sequence(lambda n: f'Lead-{n}')
    text = fuzzy.FuzzyText(length=100)
    project = factory.SubFactory(ProjectFactory)
    attachment = factory.SubFactory(FileFactory)
    published_on = fuzzy.FuzzyDate(DEFAULT_START_DATE)

    class Meta:
        model = Lead

    @factory.post_generation
    def authors(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            for author in extracted:
                self.authors.add(author)

    @factory.post_generation
    def assignee(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            for assignee in extracted:
                self.assignee.add(assignee)
                break  # Only add one assignee

    @factory.post_generation
    def emm_entities(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            for emm_entity in extracted:
                self.emm_entities.add(emm_entity)


class EmmEntityFactory(DjangoModelFactory):
    name = factory.Sequence(lambda n: f'emm-name-{n}')

    class Meta:
        model = EMMEntity


class LeadGroupFactory(DjangoModelFactory):
    title = factory.Sequence(lambda n: f'LeadGroup-{n}')

    class Meta:
        model = LeadGroup


class LeadEMMTriggerFactory(DjangoModelFactory):
    emm_keyword = factory.Sequence(lambda n: f'emm_keyword-{n}')
    emm_risk_factor = factory.Sequence(lambda n: f'emm_risk_factor-{n}')

    class Meta:
        model = LeadEMMTrigger


class LeadPreviewFactory(DjangoModelFactory):
    text_extract = factory.Faker('text', max_nb_chars=4000)

    class Meta:
        model = LeadPreview


class LeadPreviewAttachmentFactory(DjangoModelFactory):
    class Meta:
        model = LeadPreviewAttachment

    file = factory.LazyAttribute(
        lambda _: ContentFile(
            factory.django.ImageField()._make_data(
                {'width': 1024, 'height': 768}
            ), 'example.jpg'
        )
    )
    file_preview = factory.LazyAttribute(
        lambda _: ContentFile(
            factory.django.ImageField()._make_data(
                {'width': 1024, 'height': 768}
            ), 'example.jpg'
        )
    )


class UserSavedLeadFilterFactory(DjangoModelFactory):
    class Meta:
        model = UserSavedLeadFilter
