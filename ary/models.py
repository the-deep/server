from django.db import models
from django.contrib.postgres.fields import JSONField

from user_resource.models import UserResource
from deep.models import Field, FieldOption
from lead.models import Lead


class AssessmentTemplate(UserResource):
    title = models.CharField(max_length=255)

    sector_moderate_pin_tooltip = models.TextField(blank=True)
    sector_severe_pin_tooltip = models.TextField(blank=True)
    sector_pin_tooltip = models.TextField(blank=True)

    sector_priority_tooltip = models.TextField(blank=True)
    sector_affected_tooltip = models.TextField(blank=True)
    sector_specific_need_tooltip = models.TextField(blank=True)

    humanitarian_limited_tooltip = models.TextField(blank=True)
    humanitarian_restricted_tooltip = models.TextField(blank=True)
    humanitarian_access_constraints_tooltip = models.TextField(blank=True)

    humanitarian_priority_issue_tooltip = models.TextField(blank=True)
    humanitarian_affected_location_tooltip = models.TextField(blank=True)

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


class Assessment(UserResource):
    """
    Assesssment belonging to a lead
    """
    lead = models.OneToOneField(Lead)
    metadata = JSONField(default=None, blank=True, null=True)
    methodology = JSONField(default=None, blank=True, null=True)
    summary = JSONField(default=None, blank=True, null=True)

    def __str__(self):
        return str(self.lead)

    @staticmethod
    def get_for(user):
        """
        Assessment can only be accessed by users who have access to
        it's lead
        """
        return Assessment.objects.filter(
            models.Q(lead__project__members=user) |
            models.Q(lead__project__user_groups__members=user)
        ).distinct()

    def can_get(self, user):
        return self.lead.can_get(user)

    def can_modify(self, user):
        return self.lead.can_modify(user)
