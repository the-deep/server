from factory.django import DjangoModelFactory

from .models import (
    Assessment,
)


class AssessmentFactory(DjangoModelFactory):
    class Meta:
        model = Assessment
