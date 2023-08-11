import datetime
import factory
from factory import fuzzy
from factory.django import DjangoModelFactory

from assessment_registry.models import (
    Question,
    Answer,
    AssessmentRegistry,
    MethodologyAttribute,
    AdditionalDocument,
    ScoreRating,
    ScoreAnalyticalDensity,
    SummaryIssue,
    Summary,
    SummaryFocus,
    SummarySubPillarIssue,
    SummarySubDimmensionIssue,
)


class SummaryIssueFactory(DjangoModelFactory):
    class Meta:
        model = SummaryIssue


class SummaryMetaFactory(DjangoModelFactory):
    class Meta:
        model = Summary


class SummarySubPillarIssueFactory(DjangoModelFactory):
    class Meta:
        model = SummarySubPillarIssue


class SummaryFocusFactory(DjangoModelFactory):
    class Meta:
        model = SummaryFocus


class SummarySubDimmensionIssueFactory(DjangoModelFactory):
    class Meta:
        model = SummarySubDimmensionIssue


class QuestionFactory(DjangoModelFactory):
    class Meta:
        model = Question


class AnswerFactory(DjangoModelFactory):
    class Meta:
        model = Answer


class MethodologyAttributeFactory(DjangoModelFactory):
    class Meta:
        model = MethodologyAttribute


class ScoreAnalyticalDensityFactory(DjangoModelFactory):
    class Meta:
        model = ScoreAnalyticalDensity


class AdditionalDocumentFactory(DjangoModelFactory):
    class Meta:
        model = AdditionalDocument


class ScoreRatingFactory(DjangoModelFactory):
    class Meta:
        model = ScoreRating


class AssessmentRegistryFactory(DjangoModelFactory):
    bg_crisis_start_date = fuzzy.FuzzyDate(datetime.date(2023, 1, 1))
    bg_crisis_type = fuzzy.FuzzyChoice(AssessmentRegistry.CrisisType)
    bg_preparedness = fuzzy.FuzzyChoice(AssessmentRegistry.PreparednessType)
    external_support = fuzzy.FuzzyChoice(AssessmentRegistry.ExternalSupportType)
    coordinated_joint = fuzzy.FuzzyChoice(AssessmentRegistry.CoordinationType)
    details_type = fuzzy.FuzzyChoice(AssessmentRegistry.Type)
    family = fuzzy.FuzzyChoice(AssessmentRegistry.FamilyType)
    frequency = fuzzy.FuzzyChoice(AssessmentRegistry.FrequencyType)
    confidentiality = fuzzy.FuzzyChoice(AssessmentRegistry.ConfidentialityType)
    language = factory.List(AssessmentRegistry.Language)
    focuses = factory.List(AssessmentRegistry.FocusType)
    sectors = factory.List(AssessmentRegistry.SectorType)
    protection_info_mgmts = factory.List(AssessmentRegistry.ProtectionInfoType)

    class Meta:
        model = AssessmentRegistry

    @factory.post_generation
    def bg_countries(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for country in extracted:
                self.bg_countries.add(country)
