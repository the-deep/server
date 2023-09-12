import typing
import random
import datetime
import factory
from factory import fuzzy
from factory.django import DjangoModelFactory
from django.db import models

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
    SummarySubDimensionIssue,
)

DEFAULT_START_DATE = datetime.date(year=2017, month=1, day=1)


def _choices(enum: typing.Type[models.IntegerChoices]):
    """
    Get key from Django Choices
    """
    return [
        key for key, _ in enum.choices
    ]


class FuzzyChoiceList(fuzzy.FuzzyChoice):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.choices_len = None

    def fuzz(self):
        if self.choices is None:
            self.choices = list(self.choices_generator)
        if self.choices_len is None:
            self.choices_len = len(self.choices)
        value = random.sample(
            self.choices,
            random.randint(0, self.choices_len)
        )
        if self.getter is None:
            return value
        return self.getter(value)


class SummaryIssueFactory(DjangoModelFactory):

    class Meta:
        model = SummaryIssue


class SummaryMetaFactory(DjangoModelFactory):
    total_people_assessed = fuzzy.FuzzyInteger(10, 100000)
    total_dead = fuzzy.FuzzyInteger(0, 100000)
    total_injured = fuzzy.FuzzyInteger(0, 100000)
    total_missing = fuzzy.FuzzyInteger(0, 100000)
    total_people_facing_hum_access_cons = fuzzy.FuzzyInteger(0, 100000)
    percentage_of_people_facing_hum_access_cons = fuzzy.FuzzyInteger(0, 100000)

    class Meta:
        model = Summary


class SummarySubPillarIssueFactory(DjangoModelFactory):
    text = factory.Faker('text')
    order = factory.Sequence(lambda n: n)

    class Meta:
        model = SummarySubPillarIssue


class SummaryFocusFactory(DjangoModelFactory):
    sector = fuzzy.FuzzyChoice(_choices(AssessmentRegistry.SectorType))
    percentage_of_people_affected = fuzzy.FuzzyInteger(low=0)
    total_people_affected = fuzzy.FuzzyInteger(low=0)
    percentage_of_moderate = fuzzy.FuzzyInteger(low=0)
    percentage_of_severe = fuzzy.FuzzyInteger(low=0)
    percentage_of_critical = fuzzy.FuzzyInteger(low=0)
    percentage_in_need = fuzzy.FuzzyInteger(low=0)
    total_moderate = fuzzy.FuzzyInteger(low=0)
    total_severe = fuzzy.FuzzyInteger(low=0)
    total_critical = fuzzy.FuzzyInteger(low=0)
    total_in_need = fuzzy.FuzzyInteger(low=0)
    total_pop_assessed = fuzzy.FuzzyInteger(low=0)
    total_not_affected = fuzzy.FuzzyInteger(low=0)
    total_affected = fuzzy.FuzzyInteger(low=0)
    total_people_in_need = fuzzy.FuzzyInteger(low=0)
    total_people_moderately_in_need = fuzzy.FuzzyInteger(low=0)
    total_people_severly_in_need = fuzzy.FuzzyInteger(low=0)
    total_people_critically_in_need = fuzzy.FuzzyInteger(low=0)

    class Meta:
        model = SummaryFocus


class SummarySubDimensionIssueFactory(DjangoModelFactory):
    sector = fuzzy.FuzzyChoice(_choices(AssessmentRegistry.SectorType))
    text = factory.Faker('text')
    order = factory.Sequence(lambda n: n)

    class Meta:
        model = SummarySubDimensionIssue


class QuestionFactory(DjangoModelFactory):
    class Meta:
        model = Question


class AnswerFactory(DjangoModelFactory):
    answer = factory.Faker('boolean')

    class Meta:
        model = Answer


class MethodologyAttributeFactory(DjangoModelFactory):
    data_collection_technique = fuzzy.FuzzyChoice(_choices(MethodologyAttribute.CollectionTechniqueType))
    sampling_approach = fuzzy.FuzzyChoice(_choices(MethodologyAttribute.SamplingApproachType))
    proximity = fuzzy.FuzzyChoice(_choices(MethodologyAttribute.ProximityType))
    unit_of_analysis = fuzzy.FuzzyChoice(_choices(MethodologyAttribute.UnitOfAnalysisType))
    unit_of_reporting = fuzzy.FuzzyChoice(_choices(MethodologyAttribute.UnitOfReportingType))
    sampling_size = fuzzy.FuzzyInteger(low=10)

    class Meta:
        model = MethodologyAttribute


class ScoreAnalyticalDensityFactory(DjangoModelFactory):
    sector = fuzzy.FuzzyChoice(_choices(AssessmentRegistry.SectorType))
    analysis_level_covered = FuzzyChoiceList(_choices(ScoreAnalyticalDensity.AnalysisLevelCovered))
    figure_provided = FuzzyChoiceList(_choices(ScoreAnalyticalDensity.FigureProvidedByAssessment))

    class Meta:
        model = ScoreAnalyticalDensity


class AdditionalDocumentFactory(DjangoModelFactory):
    document_type = fuzzy.FuzzyChoice(_choices(AdditionalDocument.DocumentType))
    external_link = 'https://example.com/invalid-file-link'

    class Meta:
        model = AdditionalDocument


class ScoreRatingFactory(DjangoModelFactory):
    score_type = fuzzy.FuzzyChoice(_choices(ScoreRating.ScoreCriteria))
    rating = fuzzy.FuzzyChoice(_choices(ScoreRating.RatingType))
    reason = factory.Faker('text')

    class Meta:
        model = ScoreRating


class AssessmentRegistryFactory(DjangoModelFactory):
    # Metadata Group
    # -- Background Fields
    bg_crisis_start_date = fuzzy.FuzzyDate(DEFAULT_START_DATE)
    bg_crisis_type = fuzzy.FuzzyChoice(_choices(AssessmentRegistry.CrisisType))
    bg_preparedness = fuzzy.FuzzyChoice(_choices(AssessmentRegistry.PreparednessType))
    external_support = fuzzy.FuzzyChoice(_choices(AssessmentRegistry.ExternalSupportType))
    coordinated_joint = fuzzy.FuzzyChoice(_choices(AssessmentRegistry.CoordinationType))
    cost_estimates_usd = fuzzy.FuzzyInteger(low=0)

    # -- Details Field
    details_type = fuzzy.FuzzyChoice(_choices(AssessmentRegistry.Type))
    family = fuzzy.FuzzyChoice(_choices(AssessmentRegistry.FamilyType))
    frequency = fuzzy.FuzzyChoice(_choices(AssessmentRegistry.FrequencyType))
    confidentiality = fuzzy.FuzzyChoice(_choices(AssessmentRegistry.ConfidentialityType))
    language = FuzzyChoiceList(_choices(AssessmentRegistry.Language))
    no_of_pages = fuzzy.FuzzyInteger(low=0)

    # -- Dates
    data_collection_start_date = fuzzy.FuzzyDate(DEFAULT_START_DATE)
    data_collection_end_date = fuzzy.FuzzyDate(DEFAULT_START_DATE)
    publication_date = fuzzy.FuzzyDate(DEFAULT_START_DATE)

    # Additional Documents
    executive_summary = factory.Faker('text')

    # Methodology
    objectives = factory.Faker('text')
    data_collection_techniques = factory.Faker('text')
    sampling = factory.Faker('text')
    limitations = factory.Faker('text')

    # Focus
    # -- Focus Sectors
    focuses = FuzzyChoiceList(_choices(AssessmentRegistry.FocusType))
    sectors = FuzzyChoiceList(_choices(AssessmentRegistry.SectorType))
    protection_info_mgmts = FuzzyChoiceList(_choices(AssessmentRegistry.ProtectionInfoType))
    affected_groups = FuzzyChoiceList(_choices(AssessmentRegistry.AffectedGroupType))

    metadata_complete = factory.Faker('boolean')
    additional_document_complete = factory.Faker('boolean')
    focus_complete = factory.Faker('boolean')
    methodology_complete = factory.Faker('boolean')
    summary_complete = factory.Faker('boolean')
    cna_complete = factory.Faker('boolean')
    score_complete = factory.Faker('boolean')

    class Meta:
        model = AssessmentRegistry

    @factory.post_generation
    def bg_countries(self, create, extracted, **_):
        if not create:
            return

        if extracted:
            for country in extracted:
                self.bg_countries.add(  # pyright: ignore [reportGeneralTypeIssues]
                    country
                )
