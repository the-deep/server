from django.db import models
from django.contrib.postgres.fields import JSONField

from project.models import Project
from analysis_framework.models import AnalysisFramework
from user_resource.models import UserResource


class CrisisType(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.title


class QuestionBase(models.Model):
    TYPE_TEXT = 'text'
    TYPE_NUMBER = 'number'
    TYPE_DATE_AND_TIME = 'date_and_time'
    TYPE_SELECT = 'select'
    TYPE_RANK = 'rank'
    TYPE_LOCATION = 'location'
    TYPE_IMAGE = 'image'
    TYPE_AUDIO = 'audio'
    TYPE_VIDEO = 'video'
    TYPE_FILE_UPLOAD = 'file_upload'
    TYPE_BARCODE = 'barcode'
    TYPE_RANGE = 'range'

    TYPE_OPTIONS = (
        (TYPE_TEXT, 'Text'),
        (TYPE_NUMBER, 'Number'),
        (TYPE_DATE_AND_TIME, 'Date and time'),
        (TYPE_SELECT, 'Select'),
        (TYPE_RANK, 'Rank'),
        (TYPE_LOCATION, 'Location'),
        (TYPE_IMAGE, 'Image'),
        (TYPE_AUDIO, 'Audio'),
        (TYPE_VIDEO, 'Video'),
        (TYPE_FILE_UPLOAD, 'File upload'),
        (TYPE_BARCODE, 'Barcode'),
        (TYPE_RANGE, 'Range'),
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

    title = models.TextField(blank=True)
    enumerator_instruction = models.TextField(blank=True)
    respondent_instruction = models.TextField(blank=True)
    type = models.CharField(max_length=56, blank=True, choices=TYPE_OPTIONS)
    importance = models.CharField(max_length=56,
                                  blank=True,
                                  choices=IMPORTANCE_OPTIONS)
    framework_attribute = JSONField(default=None, blank=True, null=True)
    response_options = JSONField(default=None, blank=True, null=True)
    crisis_type = models.ForeignKey(CrisisType, on_delete=models.SET_NULL, null=True)
    label = models.CharField(max_length=256, blank=True)
    data_collection_technique = models.CharField(max_length=56,
                                                 blank=True,
                                                 choices=DATA_COLLECTION_TECHNIQUE_OPTIONS)
    enumerator_skill = models.CharField(max_length=56,
                                        blank=True,
                                        choices=ENUMERATOR_SKILL_OPTIONS)

    class Meta:
        abstract = True


class FrameworkQuestion(QuestionBase):
    analysis_framework = models.ForeignKey(
        AnalysisFramework, on_delete=models.CASCADE,
    )


class Questionnaire(UserResource):
    title = models.CharField(max_length=255, blank=True)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    is_archived = models.BooleanField(default=False)
    crisis_type = models.ForeignKey(CrisisType, on_delete=models.SET_NULL, null=True)
    data_collection_technique = models.CharField(max_length=56,
                                                 blank=True,
                                                 choices=QuestionBase.DATA_COLLECTION_TECHNIQUE_OPTIONS)
    enumerator_skill = models.CharField(max_length=56,
                                        blank=True,
                                        choices=QuestionBase.ENUMERATOR_SKILL_OPTIONS)

    # required duration in ms
    required_duration = models.PositiveIntegerField(blank=True)

    def __str__(self):
        return self.title


class Question(QuestionBase):
    analysis_framework = models.ForeignKey(AnalysisFramework, on_delete=models.SET_NULL, null=True)
    cloned_from = models.ForeignKey(FrameworkQuestion, on_delete=models.SET_NULL, null=True)
    questionnaire = models.ForeignKey(Questionnaire, on_delete=models.CASCADE)

