from django.db import models
from django.contrib.postgres.fields import JSONField
from django.core.exceptions import ValidationError

from user_resource.models import UserResource
from deep.models import Field, FieldOption
from lead.models import Lead, LeadGroup


class AssessmentTemplate(UserResource):
    title = models.CharField(max_length=255)

    def __str__(self):
        return self.title

    @staticmethod
    def get_for(user):
        # TODO restrict to users of ACAPS project
        return AssessmentTemplate.objects.all()

    def can_get(self, user):
        return True

    def can_modify(self, user):
        return False

    def get_parent_affected_groups(self):
        return self.affectedgroup_set.filter(parent=None)

    def get_parent_priority_sectors(self):
        return self.prioritysector_set.filter(parent=None)

    def get_parent_priority_issues(self):
        return self.priorityissue_set.filter(parent=None)


class BasicEntity(models.Model):
    title = models.CharField(max_length=255)
    order = models.IntegerField(default=1)

    def __str__(self):
        return '{}'.format(self.title)

    class Meta:
        abstract = True
        ordering = ['order']


class BasicTemplateEntity(models.Model):
    template = models.ForeignKey(AssessmentTemplate)
    title = models.CharField(max_length=255)
    order = models.IntegerField(default=1)

    def __str__(self):
        return '{} ({})'.format(self.title, self.template)

    class Meta:
        abstract = True
        ordering = ['order']


class MetadataGroup(BasicTemplateEntity):
    pass


class MetadataField(Field):
    group = models.ForeignKey(MetadataGroup, related_name='fields')
    tooltip = models.TextField(blank=True)
    order = models.IntegerField(default=1)

    def __str__(self):
        return '{} ({})'.format(self.title, self.group.template)

    class Meta(Field.Meta):
        ordering = ['order']


class MetadataOption(FieldOption):
    field = models.ForeignKey(MetadataField, related_name='options')
    order = models.IntegerField(default=1)

    def __str__(self):
        return 'Option {} for {}'.format(self.title, self.field)

    class Meta(FieldOption.Meta):
        ordering = ['order']


class MethodologyGroup(BasicTemplateEntity):
    pass


class MethodologyField(Field):
    group = models.ForeignKey(MethodologyGroup, related_name='fields')
    tooltip = models.TextField(blank=True)
    order = models.IntegerField(default=1)

    def __str__(self):
        return '{} ({})'.format(self.title, self.group.template)

    class Meta(Field.Meta):
        ordering = ['order']


class MethodologyOption(FieldOption):
    field = models.ForeignKey(MethodologyField, related_name='options')
    order = models.IntegerField(default=1)

    def __str__(self):
        return 'Option {} for {}'.format(self.title, self.field)

    class Meta(FieldOption.Meta):
        ordering = ['order']


class Sector(BasicTemplateEntity):
    pass


class Focus(BasicTemplateEntity):
    class Meta(BasicTemplateEntity.Meta):
        verbose_name_plural = 'focuses'


class AffectedGroup(BasicTemplateEntity):
    parent = models.ForeignKey('AffectedGroup',
                               related_name='children',
                               default=None, null=True, blank=True)


class PrioritySector(BasicTemplateEntity):
    parent = models.ForeignKey('PrioritySector',
                               related_name='children',
                               default=None, null=True, blank=True)


class PriorityIssue(BasicTemplateEntity):
    parent = models.ForeignKey('PriorityIssue',
                               related_name='children',
                               default=None, null=True, blank=True)


class SpecificNeedGroup(BasicTemplateEntity):
    pass


class AffectedLocation(BasicTemplateEntity):
    pass


class ScoreBucket(models.Model):
    template = models.ForeignKey(AssessmentTemplate)
    min_value = models.FloatField(default=0)
    max_value = models.FloatField(default=5)
    score = models.FloatField(default=1)

    def __str__(self):
        return '{} <= x < {} : {} ({})'.format(
            self.min_value,
            self.max_value,
            self.score,
            str(self.template),
        )

    class Meta:
        ordering = ['min_value']


class ScorePillar(BasicTemplateEntity):
    weight = models.FloatField(default=0.2)


class ScoreQuestion(BasicEntity):
    pillar = models.ForeignKey(ScorePillar, on_delete=models.CASCADE,
                               related_name='questions')
    description = models.TextField(blank=True)


class ScoreScale(models.Model):
    template = models.ForeignKey(AssessmentTemplate)
    title = models.CharField(max_length=255)
    color = models.CharField(max_length=255)
    value = models.IntegerField(default=1)
    default = models.BooleanField(default=False)

    def __str__(self):
        return '{} ({} : {}) - ({})'.format(
            self.title,
            self.value,
            self.color,
            self.template,
        )

    class Meta:
        ordering = ['value']


class ScoreMatrixPillar(BasicTemplateEntity):
    weight = models.FloatField(default=0.2)


class ScoreMatrixRow(BasicEntity):
    pillar = models.ForeignKey(ScoreMatrixPillar, on_delete=models.CASCADE,
                               related_name='rows')


class ScoreMatrixColumn(BasicEntity):
    pillar = models.ForeignKey(ScoreMatrixPillar, on_delete=models.CASCADE,
                               related_name='columns')


class ScoreMatrixScale(models.Model):
    pillar = models.ForeignKey(ScoreMatrixPillar, on_delete=models.CASCADE,
                               related_name='scales')
    row = models.ForeignKey(ScoreMatrixRow, on_delete=models.CASCADE)
    column = models.ForeignKey(ScoreMatrixColumn, on_delete=models.CASCADE)
    value = models.IntegerField(default=1)
    default = models.BooleanField(default=False)

    def __str__(self):
        return '{}-{} : {}'.format(str(self.row), str(self.column),
                                   str(self.value))

    class Meta:
        ordering = ['value']


class Assessment(UserResource):
    """
    Assesssment belonging to a lead
    """
    lead = models.OneToOneField(Lead, default=None, blank=True, null=True)
    lead_group = models.OneToOneField(LeadGroup,
                                      default=None, blank=True, null=True)
    metadata = JSONField(default=None, blank=True, null=True)
    methodology = JSONField(default=None, blank=True, null=True)
    summary = JSONField(default=None, blank=True, null=True)
    score = JSONField(default=None, blank=True, null=True)

    def __str__(self):
        return str(self.lead)

    def clean(self):
        if not self.lead and not self.lead_group:
            raise ValidationError(
                'Neither `lead` nor `lead_group` defined'
            )
        if self.lead and self.lead_group:
            raise ValidationError(
                'Assessment cannot have both `lead` and `lead_group` defined'
            )
        return super(Assessment, self).clean()

    def save(self, *args, **kwargs):
        self.clean()
        return super(Assessment, self).save(*args, **kwargs)

    @staticmethod
    def get_for(user):
        """
        Assessment can only be accessed by users who have access to
        it's lead
        """
        return Assessment.objects.filter(
            models.Q(lead__project__members=user) |
            models.Q(lead__project__user_groups__members=user) |
            models.Q(lead_group__project__members=user) |
            models.Q(lead_group__project__user_groups__members=user)
        ).distinct()

    def can_get(self, user):
        return (
            (self.lead and self.lead.can_get(user)) or
            (self.lead_group and self.lead_group.can_get(user))
        )

    def can_modify(self, user):
        return (
            (self.lead and self.lead.can_modify(user)) or
            (self.lead_group and self.lead_group.can_modify(user))
        )
