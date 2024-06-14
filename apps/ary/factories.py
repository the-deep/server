from factory.django import DjangoModelFactory

from .models import Assessment, AssessmentTemplate


class AssessmentFactory(DjangoModelFactory):
    class Meta:
        model = Assessment


class AssessmentTemplateFactory(DjangoModelFactory):
    class Meta:
        model = AssessmentTemplate
