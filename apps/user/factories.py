import factory
from factory import fuzzy
from factory.django import DjangoModelFactory

from .models import Feature, User
from .serializers import UserSerializer

PROFILE_FIELDS = ["display_picture", "organization", "language", "email_opt_outs", "last_active_project"]


class UserFactory(DjangoModelFactory):
    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    email = factory.Sequence(lambda n: f"{n}@xyz.com")
    username = factory.LazyAttribute(lambda user: user.email)
    password_text = fuzzy.FuzzyText(length=15)
    password = factory.PostGeneration(lambda user, *args, **kwargs: user.set_password(user.password_text))

    class Meta:
        model = User

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        password_text = kwargs.pop("password_text")
        profile_data = {key: kwargs.pop(key) for key in PROFILE_FIELDS if key in kwargs}
        user = super()._create(model_class, *args, **kwargs)
        UserSerializer.update_or_create_profile(user, profile_data)
        user.profile.refresh_from_db()
        user.password_text = password_text
        return user


class FeatureFactory(DjangoModelFactory):
    title = factory.PostGeneration(lambda feature, *args, **kwargs: f"Feature {feature.key}")
    feature_type = fuzzy.FuzzyChoice(Feature.FeatureType.choices, getter=lambda c: c[0])

    class Meta:
        model = Feature
