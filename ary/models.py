from django.db import models
from django.contrib.postgres.fields import JSONField
from django.core.exceptions import ValidationError

from user_resource.models import UserResource
from deep.models import Field, FieldOption
from lead.models import Lead, LeadGroup
from geo.models import GeoArea


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

    def _load_schema(self, FieldClass, GroupClass=None):
        schema = {}
        assessment_template = self.lead.project.assessment_template
        if GroupClass is not None:
            groups = GroupClass.objects.filter(template=assessment_template)
            schema = {
                group.title: [
                    {
                        'id': field.id,
                        'name': field.title,
                        'type': field.field_type,
                        'options': {
                            x['key']: x['title'] for x in field.get_options()
                        }
                    }
                    for field in group.fields.all()
                ] for group in groups
            }
        else:
            fields = FieldClass.objects.filter(template=assessment_template)
            schema = [
                {
                    'id': field.id,
                    'name': field.title,
                    'type': field.field_type,
                    'options': {
                        x['key']: x['title'] for x in field.get_options()
                    }
                }
                for field in fields
            ]
        return schema

    def _data_from_schema(self, schema, raw_data):
        if not raw_data:
            return {}
        if 'id' in schema:
            key = str(schema['id'])
            value = raw_data.get(key, '')
            if schema['type'] == Field.SELECT:
                value = schema['options'].get(value, value)
            if schema['type'] == Field.MULTISELECT:
                value = [schema['options'].get(x, x) for x in value]
            return {schema['name']: value}
        if isinstance(schema, dict):
            data = {
                k: self._data_from_schema(v, raw_data)
                for k, v in schema.items()}
        elif isinstance(schema, list):
            data = [self._data_from_schema(x, raw_data) for x in schema]
        else:
            raise Exception("Something that could not be parsed from schema")
        return data

    def get_metadata_json(self):
        metadata_schema = self._load_schema(MetadataField, MetadataGroup)
        metadata_raw = self.metadata or {}
        metadata_raw = metadata_raw.get('basic_information', {})
        metadata = self._data_from_schema(metadata_schema, metadata_raw)
        return metadata

    def get_methodology_json(self):
        methodology_sch = self._load_schema(MethodologyField, MethodologyGroup)
        methodology_raw = self.methodology or {}
        attributes_raw = methodology_raw.get('attributes', [])
        attributes = [
            self._data_from_schema(methodology_sch, x)
            for x in attributes_raw
        ]
        sectors = [
            Sector.objects.get(id=x).title
            for x in self.methodology.get('sectors', [])
        ]
        focuses = [
            Focus.objects.get(id=x).title
            for x in self.methodology.get('focuses', [])
        ]
        affected_groups = [
            x['name']
            for x in self.methodology.get('affected_groups', [])
        ]
        locations = [
            GeoArea.objects.get(id=x).title
            for x in self.methodology.get('locations', [])
        ]
        data_collection_techniques = self.methodology.get(
            'data_collection_techniques', []
        )
        objectives = self.methodology.get('objectives', [])
        sampling = self.methodology.get('sampling', [])
        limitations = self.methodology.get('limitations', [])
        methodology = {
            'Attributes': attributes,
            'Focuses': focuses,
            'Sectors': sectors,
            'Affected Groups': affected_groups,
            'Locations': locations,
            'Data Collection Techniques': data_collection_techniques,
            'Objectives': objectives,
            'Sampling': sampling,
            'Limitations': limitations
        }
        return methodology

    def get_summary_json(self):
        # functions to get exact value of an entry in summary group
        def identity(x):
            return x
        value_functions = {
            'specific_need_group': lambda x: SpecificNeedGroup.objects.get(
                id=x).title,
            'affected_group': lambda x: AffectedGroup.objects.get(id=x).title,
            'underlying_factors': identity,
            'outcomes': identity,
            'affected_location': lambda x: AffectedLocation.objects.get(
                id=x).title,
            'priority_sector': lambda x: PrioritySector.objects.get(
                id=x).title,
            'priority_issue': lambda x: PriorityIssue.objects.get(id=x).title
        }

        # Formatting of underscored keywords, by default is upper case as given
        # by default_format() function below
        formatting = {
            'priority_sector': lambda x: 'Most Unmet Needs Sectors',
            'affected_location': lambda x: 'Settings Facing Most Humanitarian Issues'  # noqa
        }

        def default_format(x):
            return ' '.join([x.title() for x in x.split('_')])

        summary_raw = self.summary
        if not summary_raw:
            return {}
        summary_data = {}
        # first pop cross_sector and humanitarian access, other are sectors
        # cross_sector = summary_raw.pop('cross_sector', {})
        # humanitarian_access = summary_raw.pop('humanitarian_access', {})
        # Add sectors data first
        for k, v in summary_raw.items():
            try:
                _, sec_id = k.split('-')
                sector = Sector.objects.get(id=sec_id).title
            # Exception because, we have cross_sector and humanitarian_access
            # in addition to "sector-<id>" keys
            except ValueError:
                sector = default_format(k)
            data = {}
            for kk, vv in v.items():
                grouping, rowindex, col = kk.split('-')
                # format them
                grouping_f = formatting.get(grouping, default_format)(grouping)
                col_f = formatting.get(col, default_format)(col)
                # get exact value
                value = value_functions[grouping](vv)

                group_data = data.get(grouping_f, {})
                # first time, initialize to list of 3 empty strings
                coldata = group_data.get(col_f, ['']*3)
                coldata[int(rowindex)] = value
                group_data[col_f] = coldata
                data[grouping_f] = group_data
            summary_data[sector] = data
        # add cross_sector
        return summary_data

    def to_exportable_json(self):
        if not self.lead:
            return {}
        # for meta data
        metadata = self.get_metadata_json()
        # for methodology
        methodology = self.get_methodology_json()
        # summary
        summary = self.get_summary_json()
        return {
            'metadata': metadata,
            'methodology': methodology,
            'summary': summary,
        }
