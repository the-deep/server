from factory.django import DjangoModelFactory

from .models import (
    AssessmentTemplate,
    Assessment,
)


class AssessmentFactory(DjangoModelFactory):
    class Meta:
        model = Assessment


class AssessmentTemplateFactory(DjangoModelFactory):
    class Meta:
        model = AssessmentTemplate
