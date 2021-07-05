import factory
from factory import fuzzy
from factory.django import DjangoModelFactory

from .models import User


class UserFactory(DjangoModelFactory):
    class Meta:
        model = User

    email = factory.Sequence(lambda n: f'{n}@xyz.com')
    username = factory.LazyAttribute(lambda user: user.email)
    password_text = fuzzy.FuzzyText(length=15)
    password = factory.PostGeneration(lambda user, *args, **kwargs: user.set_password(user.password_text))

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        password_text = kwargs.pop('password_text')
        user = super()._create(model_class, *args, **kwargs)
        user.password_text = password_text
        return user
