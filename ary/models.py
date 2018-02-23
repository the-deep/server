from django.db import models
from django.contrib.postgres.fields import JSONField

from user_resource.models import UserResource
from deep.models import Field, FieldOption
from lead.models import Lead


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


class MetadataGroup(models.Model):
    template = models.ForeignKey(AssessmentTemplate)
    title = models.CharField(max_length=255)
    order = models.IntegerField(default=1)

    def __str__(self):
        return '{} ({})'.format(self.title, self.template)

    class Meta:
        ordering = ['order']


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


class MethodologyGroup(models.Model):
    template = models.ForeignKey(AssessmentTemplate)
    title = models.CharField(max_length=255)
    order = models.IntegerField(default=1)

    def __str__(self):
        return '{} ({})'.format(self.title, self.template)

    class Meta:
        ordering = ['order']


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


class AssessmentTopic(models.Model):
    template = models.ForeignKey(AssessmentTemplate)
    title = models.CharField(max_length=255)
    order = models.IntegerField(default=1)

    def __str__(self):
        return '{} ({})'.format(self.title, self.template)

    class Meta:
        ordering = ['order']


class AffectedGroup(models.Model):
    template = models.ForeignKey(AssessmentTemplate)
    parent = models.ForeignKey('AffectedGroup',
                               related_name='children',
                               default=None, null=True, blank=True)
    title = models.CharField(max_length=255)
    order = models.IntegerField(default=1)

    def __str__(self):
        return '{} ({})'.format(self.title, self.template)

    class Meta:
        ordering = ['order']


class Assessment(UserResource):
    """
    Assesssment belonging to a lead
    """
    lead = models.ForeignKey(Lead)
    meta_data = JSONField(default=None, blank=True, null=True)
    methodology_data = JSONField(default=None, blank=True, null=True)

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
