from django.db import models
from django.contrib.postgres.fields import JSONField, ArrayField, HStoreField
from django.utils.hashable import make_hashable
from django.utils.encoding import force_str

from ordered_model.models import OrderedModel

from project.models import Project
from analysis_framework.models import AnalysisFramework
from user_resource.models import UserResource


class CrisisType(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.title


class QuestionBase(OrderedModel):
    # https://xlsform.org/en/#question-types
    TYPE_INTEGER = 'integer'
    TYPE_DECIMAL = 'decimal'
    TYPE_TEXT = 'text'
    TYPE_RANGE = 'range'

    TYPE_SELECT_ONE = 'select_one'
    TYPE_SELECT_MULTIPLE = 'select_multiple'
    TYPE_RANK = 'rank'

    TYPE_GEOPOINT = 'geopoint'
    TYPE_GEOTRACE = 'geotrace'
    TYPE_GEOSHAPE = 'geoshape'

    TYPE_DATE = 'date'
    TYPE_TIME = 'time'
    TYPE_DATETIME = 'dateTime'

    TYPE_FILE = 'file'
    TYPE_IMAGE = 'image'
    TYPE_AUDIO = 'audio'
    TYPE_VIDEO = 'video'
    TYPE_BARCODE = 'barcode'

    # TYPE_CALCULATE = 'calculate'
    # TYPE_NOTE = 'note'
    # TYPE_ACKNOWLEDGE = 'acknowledge'
    # TYPE_HIDDEN = 'hidden'

    TYPE_OPTIONS = (
        (TYPE_TEXT, 'Text'),
        (TYPE_INTEGER, 'Integer'),
        (TYPE_DECIMAL, 'Decimal'),

        (TYPE_DATE, 'Date'),
        (TYPE_TIME, 'Time'),
        (TYPE_DATETIME, 'Date and time'),

        (TYPE_SELECT_ONE, 'Select one'),
        (TYPE_SELECT_MULTIPLE, 'Select multiple'),
        (TYPE_RANK, 'Rank'),

        (TYPE_GEOPOINT, 'Geopoint'),
        (TYPE_GEOTRACE, 'Geotrace'),
        (TYPE_GEOSHAPE, 'Geoshape'),

        (TYPE_IMAGE, 'Image'),
        (TYPE_AUDIO, 'Audio'),
        (TYPE_VIDEO, 'Video'),
        (TYPE_FILE, 'Generic File'),
        (TYPE_BARCODE, 'Barcode'),
        (TYPE_RANGE, 'Range'),

        # (TYPE_CALCULATE, 'Calculate'),
        # (TYPE_NOTE, 'Note'),
        # (TYPE_ACKNOWLEDGE, 'Acknowledge'),
        # (TYPE_HIDDEN, 'Hidden'),
    )

    IMPORTANCE_1 = '1'
    IMPORTANCE_2 = '2'
    IMPORTANCE_3 = '3'
    IMPORTANCE_4 = '4'
    IMPORTANCE_5 = '5'

    IMPORTANCE_OPTIONS = (
        (IMPORTANCE_1, '1'),
        (IMPORTANCE_2, '2'),
        (IMPORTANCE_3, '3'),
        (IMPORTANCE_4, '4'),
        (IMPORTANCE_5, '5'),
    )

    # Data collection technique choices
    DIRECT = 'direct'
    FOCUS_GROUP = 'focus_group'
    ONE_ON_ONE_INTERVIEW = 'one_on_one_interviews'
    OPEN_ENDED_SURVEY = 'open_ended_survey'
    CLOSED_ENDED_SURVEY = 'closed_ended_survey'

    DATA_COLLECTION_TECHNIQUE_OPTIONS = (
        (DIRECT, 'Direct observation'),
        (FOCUS_GROUP, 'Focus group'),
        (ONE_ON_ONE_INTERVIEW, '1-on-1 interviews'),
        (OPEN_ENDED_SURVEY, 'Open-ended survey'),
        (CLOSED_ENDED_SURVEY, 'Closed-ended survey'),
    )

    # Enumerator skill choices
    BASIC = 'basic'
    MEDIUM = 'medium'

    ENUMERATOR_SKILL_OPTIONS = (
        (BASIC, 'Basic'),
        (MEDIUM, 'Medium'),
    )

    name = models.CharField(max_length=255)
    title = models.TextField(blank=True)
    more_titles = HStoreField(default=dict, blank=True, null=True)  # Titles in other languages
    enumerator_instruction = models.TextField(blank=True)
    respondent_instruction = models.TextField(blank=True)
    framework_attribute = JSONField(default=None, blank=True, null=True)
    response_options = JSONField(default=None, blank=True, null=True)
    crisis_type = models.ForeignKey(CrisisType, on_delete=models.SET_NULL, null=True)
    type = models.CharField(max_length=56, blank=True, choices=TYPE_OPTIONS)
    importance = models.CharField(max_length=56, blank=True, choices=IMPORTANCE_OPTIONS)
    data_collection_technique = models.CharField(max_length=56, blank=True, choices=DATA_COLLECTION_TECHNIQUE_OPTIONS)
    enumerator_skill = models.CharField(max_length=56, blank=True, choices=ENUMERATOR_SKILL_OPTIONS)
    # required duration in seconds
    required_duration = models.PositiveIntegerField(blank=True, null=True)

    order = models.IntegerField(default=1)
    is_required = models.BooleanField(default=False)
    is_archived = models.BooleanField(default=False)

    class Meta:
        abstract = True


class Questionnaire(UserResource):
    title = models.CharField(max_length=255, blank=True)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    is_archived = models.BooleanField(default=False)
    crisis_types = models.ManyToManyField(CrisisType, blank=True)
    data_collection_techniques = ArrayField(
        models.CharField(max_length=56, choices=QuestionBase.DATA_COLLECTION_TECHNIQUE_OPTIONS),
        default=list,
    )
    enumerator_skill = models.CharField(
        max_length=56, blank=True, choices=QuestionBase.ENUMERATOR_SKILL_OPTIONS)

    # required duration in seconds
    required_duration = models.PositiveIntegerField(blank=True, null=True)

    def __str__(self):
        return self.title

    def get_data_collection_techniques_display(self):
        choices_dict = dict(make_hashable(QuestionBase.DATA_COLLECTION_TECHNIQUE_OPTIONS))
        return [
            force_str(choices_dict.get(make_hashable(value), value), strings_only=True)
            for value in self.data_collection_techniques or []
        ]

    def can_modify(self, user):
        return self.project.can_modify(user)


class FrameworkQuestion(QuestionBase):
    analysis_framework = models.ForeignKey(
        AnalysisFramework, on_delete=models.CASCADE,
    )
    order_with_respect_to = 'analysis_framework'

    def can_modify(self, user):
        return self.analysis_framework.can_modify(user)

    def can_get(self, user):
        return self.analysis_framework.can_get(user)


class Question(QuestionBase):
    analysis_framework = models.ForeignKey(AnalysisFramework, on_delete=models.SET_NULL, null=True)
    cloned_from = models.ForeignKey(FrameworkQuestion, on_delete=models.SET_NULL, null=True)
    questionnaire = models.ForeignKey(Questionnaire, on_delete=models.CASCADE)
    order_with_respect_to = 'questionnaire'

    class Meta:
        unique_together = ('questionnaire', 'name')

    def can_modify(self, user):
        return self.questionnaire.project.can_modify(user)
