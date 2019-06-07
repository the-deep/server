from collections import OrderedDict
from django.db import models
from django.contrib.postgres.fields import JSONField
from django.core.exceptions import ValidationError

from user_resource.models import UserResource
from deep.models import Field, FieldOption
from lead.models import Lead, LeadGroup
from geo.models import GeoArea
from project.mixins import ProjectEntityMixin

from .utils import (
    FIELDS_KEYS_VALUE_EXTRACTORS,
    get_title_or_none,
    get_model_attrs_or_empty_dict,
)

from utils.common import identity, underscore_to_title


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

    def get_parent_underlying_factors(self):
        return self.underlyingfactor_set.filter(parent=None)

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
    template = models.ForeignKey(AssessmentTemplate, on_delete=models.CASCADE)
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
    group = models.ForeignKey(
        MetadataGroup, related_name='fields', on_delete=models.CASCADE,
    )
    tooltip = models.TextField(blank=True)
    order = models.IntegerField(default=1)

    def __str__(self):
        return '{} ({})'.format(self.title, self.group.template)

    class Meta(Field.Meta):
        ordering = ['order']


class MetadataOption(FieldOption):
    field = models.ForeignKey(
        MetadataField, related_name='options', on_delete=models.CASCADE,
    )
    order = models.IntegerField(default=1)

    def __str__(self):
        return 'Option {} for {}'.format(self.title, self.field)

    class Meta(FieldOption.Meta):
        ordering = ['order']


class MethodologyGroup(BasicTemplateEntity):
    pass


class MethodologyField(Field):
    group = models.ForeignKey(
        MethodologyGroup, related_name='fields', on_delete=models.CASCADE,
    )
    tooltip = models.TextField(blank=True)
    order = models.IntegerField(default=1)

    def __str__(self):
        return '{} ({})'.format(self.title, self.group.template)

    class Meta(Field.Meta):
        ordering = ['order']


class MethodologyOption(FieldOption):
    field = models.ForeignKey(
        MethodologyField, related_name='options', on_delete=models.CASCADE,
    )
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
    parent = models.ForeignKey(
        'AffectedGroup',
        related_name='children', on_delete=models.CASCADE,
        default=None, null=True, blank=True,
    )

    def get_children_list(self):
        """
        Returns list of nodes
        Each item is a dict consisting parents and node id
        Example return: [
            {'title': 'All', 'parents': ['All'], 'id': 9},
            {'title': 'All - Not Affected', 'parents': ['Not Affected', 'All'], 'id': 10},
            {'title': 'All - Affected', 'parents': ['Affected', 'All'], 'id': 1},
        ]
        """
        # TODO: cache, but very careful
        nodes_list = [
            {
                'title': self.title,
                'parents': [self.title],  # includes self as well
                'id': self.id
            }
        ]
        children = self.children.all()
        if not children:
            return nodes_list
        for child in children:
            nodes_list.extend([
                {
                    'title': f'{self.title} - {x["title"]}',
                    'parents': [*x['parents'], self.title],
                    'id': x['id']
                }
                for x in child.get_children_list()
            ])
        return nodes_list


class PrioritySector(BasicTemplateEntity):
    parent = models.ForeignKey(
        'PrioritySector',
        related_name='children', on_delete=models.CASCADE,
        default=None, null=True, blank=True,
    )

    class Meta(BasicTemplateEntity.Meta):
        verbose_name = 'sector with most unmet need'
        verbose_name_plural = 'sectors with most unmet need'


class PriorityIssue(BasicTemplateEntity):
    parent = models.ForeignKey(
        'PriorityIssue',
        related_name='children', on_delete=models.CASCADE,
        default=None, null=True, blank=True,
    )

    class Meta(BasicTemplateEntity.Meta):
        verbose_name = 'priority humanitarian access issue'


class UnderlyingFactor(BasicTemplateEntity):
    parent = models.ForeignKey(
        'UnderlyingFactor',
        related_name='children', on_delete=models.CASCADE,
        default=None, null=True, blank=True,
    )

    class Meta(BasicTemplateEntity.Meta):
        verbose_name = 'main sectoral underlying factor'


class SpecificNeedGroup(BasicTemplateEntity):
    class Meta(BasicTemplateEntity.Meta):
        verbose_name = 'priority group with specific need'
        verbose_name_plural = 'priority groups with specific need'


# TODO: Remove / This is text field now and is not required anymore
class AffectedLocation(BasicTemplateEntity):
    class Meta(BasicTemplateEntity.Meta):
        verbose_name = 'setting facing most humanitarian access issues'
        verbose_name_plural = 'settings facing most humanitarian access issues'


class ScoreBucket(models.Model):
    template = models.ForeignKey(AssessmentTemplate, on_delete=models.CASCADE)
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
    pillar = models.ForeignKey(
        ScorePillar, on_delete=models.CASCADE, related_name='questions',
    )
    description = models.TextField(blank=True)


class ScoreScale(models.Model):
    template = models.ForeignKey(AssessmentTemplate, on_delete=models.CASCADE)
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
    pillar = models.ForeignKey(
        ScoreMatrixPillar, on_delete=models.CASCADE, related_name='rows',
    )


class ScoreMatrixColumn(BasicEntity):
    pillar = models.ForeignKey(
        ScoreMatrixPillar, on_delete=models.CASCADE, related_name='columns',
    )


class ScoreMatrixScale(models.Model):
    pillar = models.ForeignKey(
        ScoreMatrixPillar, on_delete=models.CASCADE, related_name='scales',
    )
    row = models.ForeignKey(ScoreMatrixRow, on_delete=models.CASCADE)
    column = models.ForeignKey(ScoreMatrixColumn, on_delete=models.CASCADE)
    value = models.IntegerField(default=1)
    default = models.BooleanField(default=False)

    def __str__(self):
        return '{}-{} : {}'.format(str(self.row), str(self.column),
                                   str(self.value))

    class Meta:
        ordering = ['value']


class Assessment(UserResource, ProjectEntityMixin):
    """
    Assessment belonging to a lead
    """
    lead = models.OneToOneField(
        Lead, default=None, blank=True, null=True, on_delete=models.CASCADE,
    )
    project = models.ForeignKey('project.Project', on_delete=models.CASCADE)
    lead_group = models.OneToOneField(
        LeadGroup, on_delete=models.CASCADE,
        default=None, blank=True, null=True,
    )
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
        return super().clean()

    def save(self, *args, **kwargs):
        self.clean()
        return super().save(*args, **kwargs)

    def create_schema_for_group(self, GroupClass):
        schema = {}
        assessment_template = self.lead.project.assessment_template
        groups = GroupClass.objects.filter(template=assessment_template)
        schema = {
            group.title: [
                {
                    'id': field.id,
                    'name': field.title,
                    'type': field.field_type,
                    'source_type': field.source_type,
                    'options': {
                        x['key']: x['title'] for x in field.get_options()
                    }
                }
                for field in group.fields.all()
            ] for group in groups
        }
        return schema

    @staticmethod
    def get_actual_value(schema, value):
        value_function = FIELDS_KEYS_VALUE_EXTRACTORS.get(schema['name'], identity)
        if schema['type'] == Field.SELECT:
            # value should not be list but just in case it is a list
            value = value[0] if isinstance(value, list) and len(value) > 0 else value or ''
            actual_value = schema['options'].get(value, value)
        elif schema['type'] == Field.MULTISELECT:
            value = value or []
            actual_value = [
                value_function(schema['options'].get(x, x))
                for x in value
            ]
        else:
            actual_value = value
        return actual_value

    @staticmethod
    def get_data_from_schema(schema, raw_data):
        if not raw_data:
            return {}

        if 'id' in schema:
            key = str(schema['id'])
            value = raw_data.get(key, '')
            return {
                'schema': schema,
                'value': Assessment.get_actual_value(schema, value),
                'key': value,
            }
        if isinstance(schema, dict):
            data = {
                k: Assessment.get_data_from_schema(v, raw_data)
                for k, v in schema.items()
            }
        elif isinstance(schema, list):
            data = [Assessment.get_data_from_schema(x, raw_data)
                    for x in schema]
        else:
            raise Exception("Something that could not be parsed from schema")
        return data

    def get_metadata_json(self):
        metadata_schema = self.create_schema_for_group(MetadataGroup)
        metadata_raw = self.metadata or {}
        metadata_raw = metadata_raw.get('basic_information', {})
        metadata = self.get_data_from_schema(metadata_schema, metadata_raw)
        return metadata

    def get_methodology_json(self):
        methodology_sch = self.create_schema_for_group(MethodologyGroup)
        methodology_raw = self.methodology or {}

        mapping = {
            'attributes': lambda x: self.get_data_from_schema(
                methodology_sch, x
            ),
            'sectors': get_title_or_none(Sector),
            'focuses': get_title_or_none(Focus),
            'affected_groups': lambda x: {
                'key': x,
                **get_model_attrs_or_empty_dict(AffectedGroup, ['title', 'order'])(x)
            },
            'locations': get_title_or_none(GeoArea),
            'objectives': identity,
            'sampling': identity,
            'limitations': identity,
            'data_collection_techniques': identity
        }

        return {
            underscore_to_title(k):
                v if not isinstance(v, list)
                else [mapping[k](y) for y in v]
            for k, v in methodology_raw.items()
        }

    def get_summary_json(self):
        # Formatting of underscored keywords, by default is upper case as given
        # by default_format() function below
        formatting = {
            'priority_sectors': lambda x: 'Most Unmet Needs Sectors',
            'affected_location': lambda x: 'Settings Facing Most Humanitarian Issues'  # noqa
        }

        default_format = underscore_to_title   # function

        summary_raw = self.summary
        if not summary_raw:
            return {}

        summary_data = {}
        # first pop cross_sector and humanitarian access, other are sectors
        # cross_sector = summary_raw.pop('cross_sector', {})
        # humanitarian_access = summary_raw.pop('humanitarian_access', {})
        # Add sectors data first
        for sectorname, sector_data in summary_raw.items():
            try:
                _, sec_id = sectorname.split('-')
                sector = Sector.objects.get(id=sec_id).title
            # Exception because, we have cross_sector and humanitarian_access
            # in addition to "sector-<id>" keys
            except ValueError:
                sector = default_format(sectorname)

            parsed_sector_data = {}
            for groupname, group_data in sector_data.items():
                # grouping, rowindex, col = groupname.split('-')
                # format them
                grouping_f = formatting.get(groupname, default_format)(groupname)
                numrows = len(group_data.keys())

                parsed_group_data = parsed_sector_data.get(grouping_f, {})
                for rank, data in group_data.items():
                    for colname, colval in data.items():
                        col_f = formatting.get(colname, default_format)(colname)
                        group_col_data = parsed_group_data.get(
                            col_f,
                            [None] * numrows
                        )
                        rankvalue = int(rank.replace('rank', ''))  # rank<number>
                        group_col_data[rankvalue - 1] = colval

                        parsed_group_data[col_f] = group_col_data
                        parsed_sector_data[grouping_f] = parsed_group_data

            summary_data[sector] = parsed_sector_data

        # add cross_sector

        # NOTE: convert to single columned values
        # FIXME: later make the excel export highly nestable
        new_summary_data = {}
        for sector, data in summary_data.items():
            for group, groupdata in data.items():
                for col, coldata in groupdata.items():
                    key = '{} - {} - {}'.format(sector, group, col)
                    new_summary_data[key] = coldata
        return new_summary_data

    def get_score_json(self):
        if not self.score:
            return {}

        pillars_raw = self.score['pillars'] or {}
        matrix_pillars_raw = self.score['matrix_pillars'] or {}
        matrix_pillars_final_raw = {
            x: self.score[x]
            for x in self.score.keys() if 'matrix-score' in x
        }

        matrix_pillars_final_score = {}

        final_pillars_score = {}
        pillars = {}
        for pid, pdata in pillars_raw.items():
            pillar_title = get_title_or_none(ScorePillar)(pid)
            data = {}
            for qid, sid in pdata.items():
                q = get_title_or_none(ScoreQuestion)(qid)
                data[q] = get_model_attrs_or_empty_dict(ScoreScale, ['title', 'value'])(sid)
            pillars[pillar_title] = data
            final_pillars_score[pillar_title] = self.score.get('{}-score'.format(pid))

        matrix_pillars = {}
        for mpid, mpdata in matrix_pillars_raw.items():
            mpillar_title = get_title_or_none(ScoreMatrixPillar)(mpid)

            data = {}
            matrix_final_data = matrix_pillars_final_raw.get(f'{mpid}-matrix-score') or ''
            matrix_pillars_final_score[f'{mpillar_title}_final_score'] = matrix_final_data

            for sector in Sector.objects.filter(template=self.project.assessment_template):
                scale = None
                sector_id = str(sector.id)
                if sector_id in mpdata:
                    scale = ScoreMatrixScale.objects.filter(id=mpdata[sector_id]).first()
                data[sector.title] = {
                    'value': scale.value if scale else '',
                    'title': f'{scale.row.title} / {scale.column.title}' if scale else ''
                }
            matrix_pillars[mpillar_title] = data

        return {
            'final_score': self.score.get('final_score'),
            'final_pillars_score': final_pillars_score,
            'pillars': pillars,
            'matrix_pillars': matrix_pillars,
            'matrix_pillars_final_score': matrix_pillars_final_score,
        }

    def to_exportable_json(self):
        if not self.lead:
            return {}
        # for meta data
        metadata = self.get_metadata_json()
        # for methodology
        methodology = self.get_methodology_json()
        # summary
        summary = self.get_summary_json()
        # score
        score = self.get_score_json()
        return OrderedDict((
            ('metadata', metadata),
            ('methodology', methodology),
            ('summary', summary),
            ('score', score)
        ))
