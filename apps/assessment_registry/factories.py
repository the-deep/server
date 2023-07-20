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
    SummarySubSectorIssue,
    SummaryFocusSubSectorIssue,
)


class SummaryIssueFactory(DjangoModelFactory):
    class Meta:
        model = SummaryIssue


class SummaryMetaFactory(DjangoModelFactory):
    class Meta:
        model = Summary


class SummarySubSectorIssueFactory(DjangoModelFactory):
    class Meta:
        model = SummarySubSectorIssue


class SummaryFocusFactory(DjangoModelFactory):
    class Meta:
        model = SummaryFocus


class SummaryFocusSubSectorIssueFactory(DjangoModelFactory):
    class Meta:
        model = SummaryFocusSubSectorIssue


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
    matrix_score = fuzzy.FuzzyInteger(0, 10)
    final_score = fuzzy.FuzzyInteger(0, 10)

    class Meta:
        model = AssessmentRegistry

    @factory.post_generation
    def bg_countries(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for country in extracted:
                self.bg_countries.add(country)

    @factory.post_generation
    def lead_organizations(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for org in extracted:
                self.lead_organizations.add(org)

    @factory.post_generation
    def international_partners(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for partner in extracted:
                self.international_partners.add(partner)

    @factory.post_generation
    def donors(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for donor in extracted:
                self.donors.add(donor)

    @factory.post_generation
    def national_partners(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for partner in extracted:
                self.national_partners.add(partner)

    @factory.post_generation
    def governments(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for gov in extracted:
                self.governments.add(gov)
