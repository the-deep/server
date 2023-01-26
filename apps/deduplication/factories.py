from factory.django import DjangoModelFactory

from .models import LSHIndex


class LSHIndexFactory(DjangoModelFactory):
    class Meta:
        model = LSHIndex
