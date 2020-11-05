from django.utils import timezone
from django.db.models import F, Count
from entry.stats import (
    _get_project_geoareas,
    _get_lead_data,
    get_project_entries_stats
)
from apps.entry.widgets.geo_widget import get_valid_geo_ids

from organization.models import OrganizationType, Organization
from lead.models import Lead
from ary.models import (
    Assessment,
    MetadataField,
    MethodologyField,
    Focus,
    Sector,
    AffectedGroup,

    ScorePillar,
    ScoreScale,

    ScoreMatrixPillar,
    ScoreMatrixScale,
)


def _get_integer_array(array):
    if array:
        return [int(id) for id in array]
    return []


def _get_ary_field_options(config):
    pk = config['pk']
    field_type = config['type']
    if field_type == 'metadatafield':
        return list(
            MetadataField.objects.get(pk=pk).options.values('key', 'title').values(id=F('key'), name=F('title'))
        )
    elif field_type == 'methodologyfield':
        return list(
            MethodologyField.objects.get(pk=pk).options.values('key', 'title').values(id=F('key'), name=F('title'))
        )
    elif field_type == 'scorepillar':
        return list(
            ScorePillar.objects.get(pk=pk).questions.values('id', name=F('title'))
        )
    elif field_type == 'scorematrixpillar':
        return {
            'scale': list(ScoreMatrixScale.objects.filter(pillar=pk).values('id', 'row', 'column', 'value')),
        }
    raise Exception(f'Unknown field type provided {field_type}')


def get_project_ary_entry_stats(project):
    """
    NOTE: This is a custom made API for Ary VIz and might not work for all Assessment Frameworks.
    """
    # Sample config [Should work what modification if fixture is used to load]
    dynamic_fields = {
        'assessment_type': {
            'pk': 20,
            'type': 'metadatafield',
        },
        'language': {
            'pk': 18,
            'type': 'metadatafield',
        },
        'coordination': {
            'pk': 6,
            'type': 'metadatafield',
        },
        'frequency': {
            'pk': 16,
            'type': 'metadatafield',
        },

        'units': {
            'pk': 6,  # Unit of reporting
            'type': 'methodologyfield',
        },
        'type_of_unit_of_analysis': {
            'pk': 5,  # Unit of analysis
            'type': 'methodologyfield',
        },
        'sampling_approach': {
            'pk': 2,  # Sampling Approach
            'type': 'methodologyfield',
        },
        'data_collection_technique': {
            'pk': 1,  # data collection technique
            'type': 'methodologyfield',
        },

        'fit_for_purpose_array': {
            'pk': 1,
            'type': 'scorepillar',
        },
        'trustworthiness_array': {
            'pk': 2,
            'type': 'scorepillar',
        },
        'analytical_rigor_array': {
            'pk': 3,
            'type': 'scorepillar',
        },
        'analytical_writing_array': {
            'pk': 4,
            'type': 'scorepillar',
        },
        'analytical_density': {
            'pk': 1,
            'type': 'scorematrixpillar',
        },
    }

    # Stakeholder is MetaField Group [Used to identify organizations field in the stakeholder group]
    stakeholder_pk = 2
    stakeholder_fields_id = MetadataField.objects.filter(group=stakeholder_pk).values_list('id', flat=True)

    # Used to generate data for individuals and households sum
    methodology_attributes_fields = {
        'sampling_size_field_pk': 3,
        # Both are key of methodology field(unit_of_analysis)'s options
        'households': 11,
        'individuals': 12,
    }

    dynamic_meta = {
        key: _get_ary_field_options(value)
        for key, value in dynamic_fields.items() if value.get('pk')
    }

    analytical_density_scale = {
        scale['id']: scale['value']
        for scale in dynamic_meta['analytical_density']['scale']
    }

    static_meta = {
        'focus_array': list(Focus.objects.values('id', name=F('title'))),
        'sector_array': list(Sector.objects.values('id', name=F('title'))),
        'affected_groups_array': list(AffectedGroup.objects.values('id', name=F('title'))),
        'organization_type': list(
            OrganizationType.objects.annotate(
                organization_count=Count('organization', distinct=True),
            ).values(
                'id',
                'organization_count',
                name=F('title')
            )
        ),
        'organization': [
            {
                'id': org.id,
                'name': org.title,
                'short_name': org.short_name,
                'long_name': org.long_name,
                'organization_type_id': org.organization_type_id,
                'parent': org.parent_id,
            }
            for org in Organization.objects.all()
        ],
        # scale used by score_pillar
        'scorepillar_scale': list(ScoreScale.objects.values('id', 'color', 'value', name=F('title'))),
        'final_scores_array': {
            'score_pillar': list(ScorePillar.objects.values('id', name=F('title'))),
            'score_matrix_pillar': list(ScoreMatrixPillar.objects.values('id', name=F('title'))),
        },

        # NOTE: Is defined in client
        'additional_documentation_array': [
            {'id': 1, 'name': 'Executive Summary'},
            {'id': 2, 'name': 'Assessment Database'},
            {'id': 3, 'name': 'Questionnaire'},
            {'id': 4, 'name': 'Miscellaneous'},
        ],
        'methodology_content': [
            {'id': 1, 'name': 'Objectives'},
            {'id': 2, 'name': 'Data Collection Techniques'},
            {'id': 3, 'name': 'Sampling'},
            {'id': 4, 'name': 'Limitations'},
        ],
    }

    # Used to retrive organization type ID using Organiztion ID
    organization_type_map = {
        # Organization ID -> Organization Type ID
        org['id']: org['organization_type_id']
        for org in static_meta['organization']
    }

    meta = {
        'data_calculated': timezone.now(),
        **static_meta,
        **dynamic_meta,
    }
    public_data = []
    confidential_data = []

    for ary in Assessment.objects.prefetch_related('lead', 'lead__attachment').filter(project=project).all():
        metadata_raw = ary.metadata or {}
        basic_information = metadata_raw.get('basic_information') or {}
        additional_documents = metadata_raw.get('additional_documents') or {}

        methodology_raw = ary.methodology or {}
        methodology_attributes = methodology_raw.get('attributes') or []
        score_raw = ary.score or {}
        pillars = score_raw.get('pillars') or {}
        matrix_pillars = score_raw.get('matrix_pillars') or {}

        scores = {
            'final_scores': {
                'score_pillar': {
                    score_pillar['id']: score_raw.get(f"{score_pillar['id']}-score")
                    for score_pillar in meta['final_scores_array']['score_pillar']
                },
                'score_matrix_pillar': {
                    sm_pillar['id']: score_raw.get(f"{sm_pillar['id']}-matrix-score")
                    for sm_pillar in meta['final_scores_array']['score_matrix_pillar']
                }
            },

            # Analytical Density (Matrix Score Pillar)
            **{
                # key: Sector id (Food, Livelihood, Education (Selected Sectors)
                # value: Cell id
                score_matrix_pillar_key: {
                    sector_id: analytical_density_scale.get(scale_id)
                    for sector_id, scale_id in (
                        matrix_pillars.get(
                            str(dynamic_fields[score_matrix_pillar_key]['pk'])
                        ) or {}
                    ).items()
                }
                for score_matrix_pillar_key in ['analytical_density']
            },

            **{
                # NOTE: Make sure the keys don't conflit with outer keys
                scorepillar_key: {
                    option['id']: (
                        pillars.get(str(dynamic_fields[scorepillar_key]['pk'])) or {}
                    ).get(str(option['id']))
                    for option in meta[scorepillar_key]
                } for scorepillar_key in [
                    'fit_for_purpose_array',
                    'trustworthiness_array',
                    'analytical_rigor_array',
                    'analytical_writing_array',
                ]
            }
        }

        lead = ary.lead
        # Non confidential data
        lead_data = _get_lead_data(lead)

        # confidential data (if lead is confidential)
        lead_source_data = {}
        if (
            lead.source_type in [Lead.DISK, Lead.DROPBOX, Lead.GOOGLE_DRIVE] and
            lead.attachment and lead.attachment.file
        ):
            lead_source_data['attachment'] = lead.attachment.file.url
        elif lead.source_type == Lead.WEBSITE:
            lead_source_data['url'] = lead.url
        elif lead.source_type == Lead.TEXT:
            lead_source_data['text'] = lead.text

        ary_data = {
            'pk': ary.pk,
            'created_at': ary.created_at,
            'date': ary.lead.created_at,
            'lead': {
                **lead_data,
                **lead_source_data,
            },

            'focus': _get_integer_array(methodology_raw.get('focuses')),
            'sector': _get_integer_array(methodology_raw.get('sectors')),
            'scores': scores,
            'geo': get_valid_geo_ids(_get_integer_array(methodology_raw.get('locations'))),
            'affected_groups': _get_integer_array(methodology_raw.get('affected_groups')),

            'organization_and_stakeholder_type': [
                # Organization Type ID, Organization ID
                [organization_type_map.get(organization_id), organization_id]
                for field_id in stakeholder_fields_id
                for organization_id in basic_information.get(str(field_id)) or []
            ],

            # Metadata Fields Data
            **{
                key: basic_information.get(str(dynamic_fields[selector]['pk']))
                for key, selector in (
                    # NOTE: Make sure the keys are not conflicting with outer keys
                    ('assessment_type', 'assessment_type'),
                    ('language', 'language'),
                    ('coordination', 'coordination'),
                    ('frequency', 'frequency'),
                )
            },

            # Housholds and Individuals
            **{
                unit_of_analysis_type: sum(
                    attribute.get(str(methodology_attributes_fields['sampling_size_field_pk'])) or 0
                    for attribute in methodology_attributes
                    if int(
                        attribute.get(str(dynamic_fields['type_of_unit_of_analysis']['pk'])) or -1
                    ) == int(methodology_attributes_fields[unit_of_analysis_type])
                ) for unit_of_analysis_type in ['households', 'individuals']
            },

            'data_collection_technique_sample_size': {
                technique['id']: sum(
                    attribute.get(str(methodology_attributes_fields['sampling_size_field_pk'])) or 0
                    for attribute in methodology_attributes
                    if int(
                        attribute.get(str(dynamic_fields['data_collection_technique']['pk'])) or -1
                    ) == int(technique['id'])
                ) for technique in dynamic_meta['data_collection_technique']
            },

            # Methodology Fields Data
            **{
                key: [
                    attribute.get(str(dynamic_fields[selector]['pk']))
                    for attribute in methodology_attributes
                ] for key, selector in (
                    # NOTE: Make sure the keys are not conflicting with outer keys
                    ('data_collection_technique', 'data_collection_technique'),
                    ('unit_of_analysis', 'type_of_unit_of_analysis'),
                    ('unit_of_reporting', 'units'),
                    ('sampling_approach', 'sampling_approach'),
                )
            },

            'methodology_content': [
                1 if methodology_raw.get(content_type) else 0
                for content_type in ['objectives', 'data_collection_techniques', 'sampling', 'limitations']
            ],

            'additional_documentation': [
                len(additional_documents.get(doc_type) or [])
                for doc_type in ['executive_summary', 'assessment_data', 'questionnaire', 'misc']
            ],
        }
        confidential_data.append(ary_data)

        # Hide source data from confidential leads for unrestricted users
        if ary.lead.confidentiality == Lead.CONFIDENTIAL:
            public_data.append({
                **ary_data,
                'lead': lead_data,  # No source data
            })
        else:
            public_data.append(ary_data)

    entry_stats = get_project_entries_stats(project, skip_geo_data=True)
    geo_array = _get_project_geoareas(project)

    return {
        'geo_data': geo_array,
        'entry_data': entry_stats,
        'ary_data': {
            'meta': meta,
            'data': public_data,
        },
    }, {
        'geo_data': geo_array,
        'entry_data': entry_stats,
        'ary_data': {
            'meta': meta,
            'data': confidential_data,
        },
    }
