# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import GenericRepr, Snapshot


snapshots = Snapshot()

snapshots['AssistedTaggingCallbackApiTest::test_save_draft_entry final-current-model-stats'] = {
    'model_count': 1,
    'model_version_count': 1,
    'model_versions': [
        {
            'model__model_id': 'all_tags_model',
            'version': '1.0.0'
        }
    ],
    'models': [
        {
            'model_id': 'all_tags_model',
            'name': 'all_tags_model'
        }
    ],
    'tag_count': 105,
    'tags': [
        {
            'is_deprecated': False,
            'name': 'sectors',
            'tag_id': '1'
        },
        {
            'is_deprecated': False,
            'name': 'reliability',
            'tag_id': '10'
        },
        {
            'is_deprecated': False,
            'name': 'Completely reliable',
            'tag_id': '1001'
        },
        {
            'is_deprecated': False,
            'name': 'Usually reliable',
            'tag_id': '1002'
        },
        {
            'is_deprecated': False,
            'name': 'Fairly Reliable',
            'tag_id': '1003'
        },
        {
            'is_deprecated': False,
            'name': 'Unreliable',
            'tag_id': '1004'
        },
        {
            'is_deprecated': False,
            'name': 'Agriculture',
            'tag_id': '101'
        },
        {
            'is_deprecated': False,
            'name': 'Cross',
            'tag_id': '102'
        },
        {
            'is_deprecated': False,
            'name': 'Education',
            'tag_id': '103'
        },
        {
            'is_deprecated': False,
            'name': 'Food Security',
            'tag_id': '104'
        },
        {
            'is_deprecated': False,
            'name': 'subpillars_1d',
            'tag_id': '2'
        },
        {
            'is_deprecated': False,
            'name': 'Environment',
            'tag_id': '201'
        },
        {
            'is_deprecated': False,
            'name': 'Socio Cultural',
            'tag_id': '202'
        },
        {
            'is_deprecated': False,
            'name': 'Economy',
            'tag_id': '203'
        },
        {
            'is_deprecated': False,
            'name': 'Demography',
            'tag_id': '204'
        },
        {
            'is_deprecated': False,
            'name': 'Legal & Policy',
            'tag_id': '205'
        },
        {
            'is_deprecated': False,
            'name': 'Security & Stability',
            'tag_id': '206'
        },
        {
            'is_deprecated': False,
            'name': 'Politics',
            'tag_id': '207'
        },
        {
            'is_deprecated': False,
            'name': 'Type And Characteristics',
            'tag_id': '208'
        },
        {
            'is_deprecated': False,
            'name': 'Underlying/Aggravating Factors',
            'tag_id': '209'
        },
        {
            'is_deprecated': False,
            'name': 'Hazard & Threats',
            'tag_id': '210'
        },
        {
            'is_deprecated': False,
            'name': 'Type/Numbers/Movements',
            'tag_id': '212'
        },
        {
            'is_deprecated': False,
            'name': 'Push Factors',
            'tag_id': '213'
        },
        {
            'is_deprecated': False,
            'name': 'Pull Factors',
            'tag_id': '214'
        },
        {
            'is_deprecated': False,
            'name': 'Intentions',
            'tag_id': '215'
        },
        {
            'is_deprecated': False,
            'name': 'Local Integration',
            'tag_id': '216'
        },
        {
            'is_deprecated': False,
            'name': 'Injured',
            'tag_id': '217'
        },
        {
            'is_deprecated': False,
            'name': 'Missing',
            'tag_id': '218'
        },
        {
            'is_deprecated': False,
            'name': 'Dead',
            'tag_id': '219'
        },
        {
            'is_deprecated': False,
            'name': 'Relief To Population',
            'tag_id': '220'
        },
        {
            'is_deprecated': False,
            'name': 'Population To Relief',
            'tag_id': '221'
        },
        {
            'is_deprecated': False,
            'name': 'Physical Constraints',
            'tag_id': '222'
        },
        {
            'is_deprecated': False,
            'name': 'Number Of People Facing Humanitarian Access Constraints/Humanitarian Access Gaps',
            'tag_id': '223'
        },
        {
            'is_deprecated': False,
            'name': 'Communication Means And Preferences',
            'tag_id': '224'
        },
        {
            'is_deprecated': False,
            'name': 'Information Challenges And Barriers',
            'tag_id': '225'
        },
        {
            'is_deprecated': False,
            'name': 'Knowledge And Info Gaps (Pop)',
            'tag_id': '226'
        },
        {
            'is_deprecated': False,
            'name': 'Knowledge And Info Gaps (Hum)',
            'tag_id': '227'
        },
        {
            'is_deprecated': False,
            'name': 'Cases',
            'tag_id': '228'
        },
        {
            'is_deprecated': False,
            'name': 'Contact Tracing',
            'tag_id': '229'
        },
        {
            'is_deprecated': False,
            'name': 'Deaths',
            'tag_id': '230'
        },
        {
            'is_deprecated': False,
            'name': 'Hospitalization & Care',
            'tag_id': '231'
        },
        {
            'is_deprecated': False,
            'name': 'Restriction Measures',
            'tag_id': '232'
        },
        {
            'is_deprecated': False,
            'name': 'Testing',
            'tag_id': '233'
        },
        {
            'is_deprecated': False,
            'name': 'Vaccination',
            'tag_id': '234'
        },
        {
            'is_deprecated': False,
            'name': 'subpillars_2d',
            'tag_id': '3'
        },
        {
            'is_deprecated': False,
            'name': 'Number Of People At Risk',
            'tag_id': '301'
        },
        {
            'is_deprecated': False,
            'name': 'Risk And Vulnerabilities',
            'tag_id': '302'
        },
        {
            'is_deprecated': False,
            'name': 'International Response',
            'tag_id': '303'
        },
        {
            'is_deprecated': False,
            'name': 'Local Response',
            'tag_id': '304'
        },
        {
            'is_deprecated': False,
            'name': 'National Response',
            'tag_id': '305'
        },
        {
            'is_deprecated': False,
            'name': 'Number Of People Reached/Response Gaps',
            'tag_id': '306'
        },
        {
            'is_deprecated': False,
            'name': 'Coping Mechanisms',
            'tag_id': '307'
        },
        {
            'is_deprecated': False,
            'name': 'Living Standards',
            'tag_id': '308'
        },
        {
            'is_deprecated': False,
            'name': 'Number Of People In Need',
            'tag_id': '309'
        },
        {
            'is_deprecated': False,
            'name': 'Physical And Mental Well Being',
            'tag_id': '310'
        },
        {
            'is_deprecated': False,
            'name': 'Driver/Aggravating Factors',
            'tag_id': '311'
        },
        {
            'is_deprecated': False,
            'name': 'Impact On People',
            'tag_id': '312'
        },
        {
            'is_deprecated': False,
            'name': 'Impact On Systems, Services And Networks',
            'tag_id': '313'
        },
        {
            'is_deprecated': False,
            'name': 'Number Of People Affected',
            'tag_id': '314'
        },
        {
            'is_deprecated': False,
            'name': 'Expressed By Humanitarian Staff',
            'tag_id': '315'
        },
        {
            'is_deprecated': False,
            'name': 'Expressed By Population',
            'tag_id': '316'
        },
        {
            'is_deprecated': False,
            'name': 'Expressed By Humanitarian Staff',
            'tag_id': '317'
        },
        {
            'is_deprecated': False,
            'name': 'Expressed By Population',
            'tag_id': '318'
        },
        {
            'is_deprecated': False,
            'name': 'specific_needs_groups',
            'tag_id': '4'
        },
        {
            'is_deprecated': False,
            'name': 'Child Head of Household',
            'tag_id': '401'
        },
        {
            'is_deprecated': False,
            'name': 'Chronically Ill',
            'tag_id': '402'
        },
        {
            'is_deprecated': False,
            'name': 'Elderly Head of Household',
            'tag_id': '403'
        },
        {
            'is_deprecated': False,
            'name': 'Female Head of Household',
            'tag_id': '404'
        },
        {
            'is_deprecated': False,
            'name': 'GBV survivors',
            'tag_id': '405'
        },
        {
            'is_deprecated': False,
            'name': 'Indigenous people',
            'tag_id': '406'
        },
        {
            'is_deprecated': False,
            'name': 'LGBTQI+',
            'tag_id': '407'
        },
        {
            'is_deprecated': False,
            'name': 'Minorities',
            'tag_id': '408'
        },
        {
            'is_deprecated': False,
            'name': 'Persons with Disability',
            'tag_id': '409'
        },
        {
            'is_deprecated': False,
            'name': 'Pregnant or Lactating Women',
            'tag_id': '410'
        },
        {
            'is_deprecated': False,
            'name': 'Single Women (including Widows)',
            'tag_id': '411'
        },
        {
            'is_deprecated': False,
            'name': 'Unaccompanied or Separated Children',
            'tag_id': '412'
        },
        {
            'is_deprecated': False,
            'name': 'gender',
            'tag_id': '5'
        },
        {
            'is_deprecated': False,
            'name': 'Female',
            'tag_id': '501'
        },
        {
            'is_deprecated': False,
            'name': 'Male',
            'tag_id': '502'
        },
        {
            'is_deprecated': False,
            'name': 'age',
            'tag_id': '6'
        },
        {
            'is_deprecated': False,
            'name': 'Adult (18 to 59 years old)',
            'tag_id': '601'
        },
        {
            'is_deprecated': False,
            'name': 'Children/Youth (5 to 17 years old)',
            'tag_id': '602'
        },
        {
            'is_deprecated': False,
            'name': 'Infants/Toddlers (<5 years old)',
            'tag_id': '603'
        },
        {
            'is_deprecated': False,
            'name': 'Older Persons (60+ years old)',
            'tag_id': '604'
        },
        {
            'is_deprecated': False,
            'name': 'severity',
            'tag_id': '7'
        },
        {
            'is_deprecated': False,
            'name': 'Critical',
            'tag_id': '701'
        },
        {
            'is_deprecated': False,
            'name': 'Major',
            'tag_id': '702'
        },
        {
            'is_deprecated': False,
            'name': 'Minor Problem',
            'tag_id': '703'
        },
        {
            'is_deprecated': False,
            'name': 'No problem',
            'tag_id': '704'
        },
        {
            'is_deprecated': False,
            'name': 'Of Concern',
            'tag_id': '705'
        },
        {
            'is_deprecated': False,
            'name': 'affected_groups',
            'tag_id': '8'
        },
        {
            'is_deprecated': False,
            'name': 'Asylum Seekers',
            'tag_id': '801'
        },
        {
            'is_deprecated': False,
            'name': 'Host',
            'tag_id': '802'
        },
        {
            'is_deprecated': False,
            'name': 'IDP',
            'tag_id': '803'
        },
        {
            'is_deprecated': False,
            'name': 'Migrants',
            'tag_id': '804'
        },
        {
            'is_deprecated': False,
            'name': 'Refugees',
            'tag_id': '805'
        },
        {
            'is_deprecated': False,
            'name': 'Returnees',
            'tag_id': '806'
        },
        {
            'is_deprecated': False,
            'name': 'demographic_group',
            'tag_id': '9'
        },
        {
            'is_deprecated': False,
            'name': 'Infants/Toddlers (<5 years old) ',
            'tag_id': '901'
        },
        {
            'is_deprecated': False,
            'name': 'Female Children/Youth (5 to 17 years old)',
            'tag_id': '902'
        },
        {
            'is_deprecated': False,
            'name': 'Male Children/Youth (5 to 17 years old)',
            'tag_id': '903'
        },
        {
            'is_deprecated': False,
            'name': 'Female Adult (18 to 59 years old)',
            'tag_id': '904'
        },
        {
            'is_deprecated': False,
            'name': 'Male Adult (18 to 59 years old)',
            'tag_id': '905'
        },
        {
            'is_deprecated': False,
            'name': 'Female Older Persons (60+ years old)',
            'tag_id': '906'
        },
        {
            'is_deprecated': False,
            'name': 'Male Older Persons (60+ years old)',
            'tag_id': '907'
        }
    ]
}

snapshots['AssistedTaggingCallbackApiTest::test_save_draft_entry final-current-prediction-stats'] = {
    'prediction_count': 72,
    'predictions': [
        {
            'category__tag_id': '1',
            'data_type': 1,
            'draft_entry__excerpt': 'sample excerpt 101',
            'is_selected': False,
            'model_version__model__model_id': 'all_tags_model',
            'prediction': GenericRepr("Decimal('0.00200000000000000004')"),
            'tag__tag_id': '101',
            'threshold': GenericRepr("Decimal('0.14000000000000001332')"),
            'value': ''
        },
        {
            'category__tag_id': '1',
            'data_type': 1,
            'draft_entry__excerpt': 'sample excerpt 101',
            'is_selected': True,
            'model_version__model__model_id': 'all_tags_model',
            'prediction': GenericRepr("Decimal('0.64800000000000002043')"),
            'tag__tag_id': '102',
            'threshold': GenericRepr("Decimal('0.17000000000000001221')"),
            'value': ''
        },
        {
            'category__tag_id': '1',
            'data_type': 1,
            'draft_entry__excerpt': 'sample excerpt 101',
            'is_selected': False,
            'model_version__model__model_id': 'all_tags_model',
            'prediction': GenericRepr("Decimal('0.02699999999999999969')"),
            'tag__tag_id': '103',
            'threshold': GenericRepr("Decimal('0.10000000000000000555')"),
            'value': ''
        },
        {
            'category__tag_id': '1',
            'data_type': 1,
            'draft_entry__excerpt': 'sample excerpt 101',
            'is_selected': False,
            'model_version__model__model_id': 'all_tags_model',
            'prediction': GenericRepr("Decimal('0.06199999999999999956')"),
            'tag__tag_id': '104',
            'threshold': GenericRepr("Decimal('0.14000000000000001332')"),
            'value': ''
        },
        {
            'category__tag_id': '2',
            'data_type': 1,
            'draft_entry__excerpt': 'sample excerpt 101',
            'is_selected': False,
            'model_version__model__model_id': 'all_tags_model',
            'prediction': GenericRepr("Decimal('0.00700000000000000015')"),
            'tag__tag_id': '204',
            'threshold': GenericRepr("Decimal('0.14000000000000001332')"),
            'value': ''
        },
        {
            'category__tag_id': '2',
            'data_type': 1,
            'draft_entry__excerpt': 'sample excerpt 101',
            'is_selected': True,
            'model_version__model__model_id': 'all_tags_model',
            'prediction': GenericRepr("Decimal('0.45800000000000001821')"),
            'tag__tag_id': '209',
            'threshold': GenericRepr("Decimal('0.05000000000000000278')"),
            'value': ''
        },
        {
            'category__tag_id': '2',
            'data_type': 1,
            'draft_entry__excerpt': 'sample excerpt 101',
            'is_selected': False,
            'model_version__model__model_id': 'all_tags_model',
            'prediction': GenericRepr("Decimal('0.00100000000000000002')"),
            'tag__tag_id': '214',
            'threshold': GenericRepr("Decimal('0.08999999999999999667')"),
            'value': ''
        },
        {
            'category__tag_id': '2',
            'data_type': 1,
            'draft_entry__excerpt': 'sample excerpt 101',
            'is_selected': False,
            'model_version__model__model_id': 'all_tags_model',
            'prediction': GenericRepr("Decimal('0.00300000000000000006')"),
            'tag__tag_id': '216',
            'threshold': GenericRepr("Decimal('0.13000000000000000444')"),
            'value': ''
        },
        {
            'category__tag_id': '2',
            'data_type': 1,
            'draft_entry__excerpt': 'sample excerpt 101',
            'is_selected': False,
            'model_version__model__model_id': 'all_tags_model',
            'prediction': GenericRepr("Decimal('0.00100000000000000002')"),
            'tag__tag_id': '217',
            'threshold': GenericRepr("Decimal('0.04000000000000000083')"),
            'value': ''
        },
        {
            'category__tag_id': '2',
            'data_type': 1,
            'draft_entry__excerpt': 'sample excerpt 101',
            'is_selected': False,
            'model_version__model__model_id': 'all_tags_model',
            'prediction': GenericRepr("Decimal('0.00400000000000000008')"),
            'tag__tag_id': '218',
            'threshold': GenericRepr("Decimal('0.08999999999999999667')"),
            'value': ''
        },
        {
            'category__tag_id': '2',
            'data_type': 1,
            'draft_entry__excerpt': 'sample excerpt 101',
            'is_selected': False,
            'model_version__model__model_id': 'all_tags_model',
            'prediction': GenericRepr("Decimal('0.00300000000000000006')"),
            'tag__tag_id': '219',
            'threshold': GenericRepr("Decimal('0.13000000000000000444')"),
            'value': ''
        },
        {
            'category__tag_id': '3',
            'data_type': 1,
            'draft_entry__excerpt': 'sample excerpt 101',
            'is_selected': False,
            'model_version__model__model_id': 'all_tags_model',
            'prediction': GenericRepr("Decimal('0.00100000000000000002')"),
            'tag__tag_id': '301',
            'threshold': GenericRepr("Decimal('0.01000000000000000021')"),
            'value': ''
        },
        {
            'category__tag_id': '3',
            'data_type': 1,
            'draft_entry__excerpt': 'sample excerpt 101',
            'is_selected': False,
            'model_version__model__model_id': 'all_tags_model',
            'prediction': GenericRepr("Decimal('0.00100000000000000002')"),
            'tag__tag_id': '302',
            'threshold': GenericRepr("Decimal('0.11000000000000000056')"),
            'value': ''
        },
        {
            'category__tag_id': '3',
            'data_type': 1,
            'draft_entry__excerpt': 'sample excerpt 101',
            'is_selected': False,
            'model_version__model__model_id': 'all_tags_model',
            'prediction': GenericRepr("Decimal('0.08300000000000000433')"),
            'tag__tag_id': '303',
            'threshold': GenericRepr("Decimal('0.38000000000000000444')"),
            'value': ''
        },
        {
            'category__tag_id': '3',
            'data_type': 1,
            'draft_entry__excerpt': 'sample excerpt 101',
            'is_selected': True,
            'model_version__model__model_id': 'all_tags_model',
            'prediction': GenericRepr("Decimal('0.08599999999999999312')"),
            'tag__tag_id': '304',
            'threshold': GenericRepr("Decimal('0.01000000000000000021')"),
            'value': ''
        },
        {
            'category__tag_id': '3',
            'data_type': 1,
            'draft_entry__excerpt': 'sample excerpt 101',
            'is_selected': False,
            'model_version__model__model_id': 'all_tags_model',
            'prediction': GenericRepr("Decimal('0.00300000000000000006')"),
            'tag__tag_id': '315',
            'threshold': GenericRepr("Decimal('0.45000000000000001110')"),
            'value': ''
        },
        {
            'category__tag_id': '3',
            'data_type': 1,
            'draft_entry__excerpt': 'sample excerpt 101',
            'is_selected': False,
            'model_version__model__model_id': 'all_tags_model',
            'prediction': GenericRepr("Decimal('0.00100000000000000002')"),
            'tag__tag_id': '316',
            'threshold': GenericRepr("Decimal('0.05999999999999999778')"),
            'value': ''
        },
        {
            'category__tag_id': '3',
            'data_type': 1,
            'draft_entry__excerpt': 'sample excerpt 101',
            'is_selected': False,
            'model_version__model__model_id': 'all_tags_model',
            'prediction': GenericRepr("Decimal('0.00400000000000000008')"),
            'tag__tag_id': '317',
            'threshold': GenericRepr("Decimal('0.28000000000000002665')"),
            'value': ''
        },
        {
            'category__tag_id': '3',
            'data_type': 1,
            'draft_entry__excerpt': 'sample excerpt 101',
            'is_selected': False,
            'model_version__model__model_id': 'all_tags_model',
            'prediction': GenericRepr("Decimal('0E-20')"),
            'tag__tag_id': '318',
            'threshold': GenericRepr("Decimal('0.13000000000000000444')"),
            'value': ''
        },
        {
            'category__tag_id': '4',
            'data_type': 1,
            'draft_entry__excerpt': 'sample excerpt 101',
            'is_selected': False,
            'model_version__model__model_id': 'all_tags_model',
            'prediction': GenericRepr("Decimal('0.00100000000000000002')"),
            'tag__tag_id': '401',
            'threshold': GenericRepr("Decimal('0.28999999999999998002')"),
            'value': ''
        },
        {
            'category__tag_id': '4',
            'data_type': 1,
            'draft_entry__excerpt': 'sample excerpt 101',
            'is_selected': False,
            'model_version__model__model_id': 'all_tags_model',
            'prediction': GenericRepr("Decimal('0.00100000000000000002')"),
            'tag__tag_id': '402',
            'threshold': GenericRepr("Decimal('0.45000000000000001110')"),
            'value': ''
        },
        {
            'category__tag_id': '4',
            'data_type': 1,
            'draft_entry__excerpt': 'sample excerpt 101',
            'is_selected': False,
            'model_version__model__model_id': 'all_tags_model',
            'prediction': GenericRepr("Decimal('0E-20')"),
            'tag__tag_id': '407',
            'threshold': GenericRepr("Decimal('0.07000000000000000666')"),
            'value': ''
        },
        {
            'category__tag_id': '4',
            'data_type': 1,
            'draft_entry__excerpt': 'sample excerpt 101',
            'is_selected': False,
            'model_version__model__model_id': 'all_tags_model',
            'prediction': GenericRepr("Decimal('0.00100000000000000002')"),
            'tag__tag_id': '408',
            'threshold': GenericRepr("Decimal('0.11000000000000000056')"),
            'value': ''
        },
        {
            'category__tag_id': '4',
            'data_type': 1,
            'draft_entry__excerpt': 'sample excerpt 101',
            'is_selected': False,
            'model_version__model__model_id': 'all_tags_model',
            'prediction': GenericRepr("Decimal('0E-20')"),
            'tag__tag_id': '412',
            'threshold': GenericRepr("Decimal('0.35999999999999998668')"),
            'value': ''
        },
        {
            'category__tag_id': '5',
            'data_type': 1,
            'draft_entry__excerpt': 'sample excerpt 101',
            'is_selected': False,
            'model_version__model__model_id': 'all_tags_model',
            'prediction': GenericRepr("Decimal('0E-20')"),
            'tag__tag_id': '501',
            'threshold': GenericRepr("Decimal('0.45000000000000001110')"),
            'value': ''
        },
        {
            'category__tag_id': '5',
            'data_type': 1,
            'draft_entry__excerpt': 'sample excerpt 101',
            'is_selected': False,
            'model_version__model__model_id': 'all_tags_model',
            'prediction': GenericRepr("Decimal('0E-20')"),
            'tag__tag_id': '502',
            'threshold': GenericRepr("Decimal('0.47999999999999998224')"),
            'value': ''
        },
        {
            'category__tag_id': '6',
            'data_type': 1,
            'draft_entry__excerpt': 'sample excerpt 101',
            'is_selected': False,
            'model_version__model__model_id': 'all_tags_model',
            'prediction': GenericRepr("Decimal('0E-20')"),
            'tag__tag_id': '601',
            'threshold': GenericRepr("Decimal('0.05999999999999999778')"),
            'value': ''
        },
        {
            'category__tag_id': '6',
            'data_type': 1,
            'draft_entry__excerpt': 'sample excerpt 101',
            'is_selected': False,
            'model_version__model__model_id': 'all_tags_model',
            'prediction': GenericRepr("Decimal('0.00100000000000000002')"),
            'tag__tag_id': '602',
            'threshold': GenericRepr("Decimal('0.47999999999999998224')"),
            'value': ''
        },
        {
            'category__tag_id': '6',
            'data_type': 1,
            'draft_entry__excerpt': 'sample excerpt 101',
            'is_selected': False,
            'model_version__model__model_id': 'all_tags_model',
            'prediction': GenericRepr("Decimal('0.02199999999999999872')"),
            'tag__tag_id': '603',
            'threshold': GenericRepr("Decimal('0.34000000000000002442')"),
            'value': ''
        },
        {
            'category__tag_id': '6',
            'data_type': 1,
            'draft_entry__excerpt': 'sample excerpt 101',
            'is_selected': False,
            'model_version__model__model_id': 'all_tags_model',
            'prediction': GenericRepr("Decimal('0E-20')"),
            'tag__tag_id': '604',
            'threshold': GenericRepr("Decimal('0.16000000000000000333')"),
            'value': ''
        },
        {
            'category__tag_id': '7',
            'data_type': 1,
            'draft_entry__excerpt': 'sample excerpt 101',
            'is_selected': False,
            'model_version__model__model_id': 'all_tags_model',
            'prediction': GenericRepr("Decimal('0.00800000000000000017')"),
            'tag__tag_id': '701',
            'threshold': GenericRepr("Decimal('0.27000000000000001776')"),
            'value': ''
        },
        {
            'category__tag_id': '8',
            'data_type': 1,
            'draft_entry__excerpt': 'sample excerpt 101',
            'is_selected': False,
            'model_version__model__model_id': 'all_tags_model',
            'prediction': GenericRepr("Decimal('0E-20')"),
            'tag__tag_id': '801',
            'threshold': GenericRepr("Decimal('0.66000000000000003109')"),
            'value': ''
        },
        {
            'category__tag_id': '8',
            'data_type': 1,
            'draft_entry__excerpt': 'sample excerpt 101',
            'is_selected': False,
            'model_version__model__model_id': 'all_tags_model',
            'prediction': GenericRepr("Decimal('0E-20')"),
            'tag__tag_id': '802',
            'threshold': GenericRepr("Decimal('0.29999999999999998890')"),
            'value': ''
        },
        {
            'category__tag_id': '9',
            'data_type': 1,
            'draft_entry__excerpt': 'sample excerpt 101',
            'is_selected': False,
            'model_version__model__model_id': 'all_tags_model',
            'prediction': GenericRepr("Decimal('-1.00000000000000000000')"),
            'tag__tag_id': '904',
            'threshold': GenericRepr("Decimal('-1.00000000000000000000')"),
            'value': ''
        },
        {
            'category__tag_id': '9',
            'data_type': 1,
            'draft_entry__excerpt': 'sample excerpt 101',
            'is_selected': False,
            'model_version__model__model_id': 'all_tags_model',
            'prediction': GenericRepr("Decimal('-1.00000000000000000000')"),
            'tag__tag_id': '905',
            'threshold': GenericRepr("Decimal('-1.00000000000000000000')"),
            'value': ''
        },
        {
            'category__tag_id': '9',
            'data_type': 1,
            'draft_entry__excerpt': 'sample excerpt 101',
            'is_selected': False,
            'model_version__model__model_id': 'all_tags_model',
            'prediction': GenericRepr("Decimal('-1.00000000000000000000')"),
            'tag__tag_id': '907',
            'threshold': GenericRepr("Decimal('-1.00000000000000000000')"),
            'value': ''
        },
        {
            'category__tag_id': '1',
            'data_type': 1,
            'draft_entry__excerpt': 'sample excerpt 102',
            'is_selected': False,
            'model_version__model__model_id': 'all_tags_model',
            'prediction': GenericRepr("Decimal('0.00200000000000000004')"),
            'tag__tag_id': '101',
            'threshold': GenericRepr("Decimal('0.14000000000000001332')"),
            'value': ''
        },
        {
            'category__tag_id': '1',
            'data_type': 1,
            'draft_entry__excerpt': 'sample excerpt 102',
            'is_selected': True,
            'model_version__model__model_id': 'all_tags_model',
            'prediction': GenericRepr("Decimal('0.64800000000000002043')"),
            'tag__tag_id': '102',
            'threshold': GenericRepr("Decimal('0.17000000000000001221')"),
            'value': ''
        },
        {
            'category__tag_id': '1',
            'data_type': 1,
            'draft_entry__excerpt': 'sample excerpt 102',
            'is_selected': False,
            'model_version__model__model_id': 'all_tags_model',
            'prediction': GenericRepr("Decimal('0.02699999999999999969')"),
            'tag__tag_id': '103',
            'threshold': GenericRepr("Decimal('0.10000000000000000555')"),
            'value': ''
        },
        {
            'category__tag_id': '1',
            'data_type': 1,
            'draft_entry__excerpt': 'sample excerpt 102',
            'is_selected': False,
            'model_version__model__model_id': 'all_tags_model',
            'prediction': GenericRepr("Decimal('0.06199999999999999956')"),
            'tag__tag_id': '104',
            'threshold': GenericRepr("Decimal('0.14000000000000001332')"),
            'value': ''
        },
        {
            'category__tag_id': '2',
            'data_type': 1,
            'draft_entry__excerpt': 'sample excerpt 102',
            'is_selected': False,
            'model_version__model__model_id': 'all_tags_model',
            'prediction': GenericRepr("Decimal('0.00700000000000000015')"),
            'tag__tag_id': '204',
            'threshold': GenericRepr("Decimal('0.14000000000000001332')"),
            'value': ''
        },
        {
            'category__tag_id': '2',
            'data_type': 1,
            'draft_entry__excerpt': 'sample excerpt 102',
            'is_selected': True,
            'model_version__model__model_id': 'all_tags_model',
            'prediction': GenericRepr("Decimal('0.45800000000000001821')"),
            'tag__tag_id': '209',
            'threshold': GenericRepr("Decimal('0.05000000000000000278')"),
            'value': ''
        },
        {
            'category__tag_id': '2',
            'data_type': 1,
            'draft_entry__excerpt': 'sample excerpt 102',
            'is_selected': False,
            'model_version__model__model_id': 'all_tags_model',
            'prediction': GenericRepr("Decimal('0.00100000000000000002')"),
            'tag__tag_id': '214',
            'threshold': GenericRepr("Decimal('0.08999999999999999667')"),
            'value': ''
        },
        {
            'category__tag_id': '2',
            'data_type': 1,
            'draft_entry__excerpt': 'sample excerpt 102',
            'is_selected': False,
            'model_version__model__model_id': 'all_tags_model',
            'prediction': GenericRepr("Decimal('0.00300000000000000006')"),
            'tag__tag_id': '216',
            'threshold': GenericRepr("Decimal('0.13000000000000000444')"),
            'value': ''
        },
        {
            'category__tag_id': '2',
            'data_type': 1,
            'draft_entry__excerpt': 'sample excerpt 102',
            'is_selected': False,
            'model_version__model__model_id': 'all_tags_model',
            'prediction': GenericRepr("Decimal('0.00100000000000000002')"),
            'tag__tag_id': '217',
            'threshold': GenericRepr("Decimal('0.04000000000000000083')"),
            'value': ''
        },
        {
            'category__tag_id': '2',
            'data_type': 1,
            'draft_entry__excerpt': 'sample excerpt 102',
            'is_selected': False,
            'model_version__model__model_id': 'all_tags_model',
            'prediction': GenericRepr("Decimal('0.00400000000000000008')"),
            'tag__tag_id': '218',
            'threshold': GenericRepr("Decimal('0.08999999999999999667')"),
            'value': ''
        },
        {
            'category__tag_id': '2',
            'data_type': 1,
            'draft_entry__excerpt': 'sample excerpt 102',
            'is_selected': False,
            'model_version__model__model_id': 'all_tags_model',
            'prediction': GenericRepr("Decimal('0.00300000000000000006')"),
            'tag__tag_id': '219',
            'threshold': GenericRepr("Decimal('0.13000000000000000444')"),
            'value': ''
        },
        {
            'category__tag_id': '3',
            'data_type': 1,
            'draft_entry__excerpt': 'sample excerpt 102',
            'is_selected': False,
            'model_version__model__model_id': 'all_tags_model',
            'prediction': GenericRepr("Decimal('0.00100000000000000002')"),
            'tag__tag_id': '301',
            'threshold': GenericRepr("Decimal('0.01000000000000000021')"),
            'value': ''
        },
        {
            'category__tag_id': '3',
            'data_type': 1,
            'draft_entry__excerpt': 'sample excerpt 102',
            'is_selected': False,
            'model_version__model__model_id': 'all_tags_model',
            'prediction': GenericRepr("Decimal('0.00100000000000000002')"),
            'tag__tag_id': '302',
            'threshold': GenericRepr("Decimal('0.11000000000000000056')"),
            'value': ''
        },
        {
            'category__tag_id': '3',
            'data_type': 1,
            'draft_entry__excerpt': 'sample excerpt 102',
            'is_selected': False,
            'model_version__model__model_id': 'all_tags_model',
            'prediction': GenericRepr("Decimal('0.08300000000000000433')"),
            'tag__tag_id': '303',
            'threshold': GenericRepr("Decimal('0.38000000000000000444')"),
            'value': ''
        },
        {
            'category__tag_id': '3',
            'data_type': 1,
            'draft_entry__excerpt': 'sample excerpt 102',
            'is_selected': True,
            'model_version__model__model_id': 'all_tags_model',
            'prediction': GenericRepr("Decimal('0.08599999999999999312')"),
            'tag__tag_id': '304',
            'threshold': GenericRepr("Decimal('0.01000000000000000021')"),
            'value': ''
        },
        {
            'category__tag_id': '3',
            'data_type': 1,
            'draft_entry__excerpt': 'sample excerpt 102',
            'is_selected': False,
            'model_version__model__model_id': 'all_tags_model',
            'prediction': GenericRepr("Decimal('0.00300000000000000006')"),
            'tag__tag_id': '315',
            'threshold': GenericRepr("Decimal('0.45000000000000001110')"),
            'value': ''
        },
        {
            'category__tag_id': '3',
            'data_type': 1,
            'draft_entry__excerpt': 'sample excerpt 102',
            'is_selected': False,
            'model_version__model__model_id': 'all_tags_model',
            'prediction': GenericRepr("Decimal('0.00100000000000000002')"),
            'tag__tag_id': '316',
            'threshold': GenericRepr("Decimal('0.05999999999999999778')"),
            'value': ''
        },
        {
            'category__tag_id': '3',
            'data_type': 1,
            'draft_entry__excerpt': 'sample excerpt 102',
            'is_selected': False,
            'model_version__model__model_id': 'all_tags_model',
            'prediction': GenericRepr("Decimal('0.00400000000000000008')"),
            'tag__tag_id': '317',
            'threshold': GenericRepr("Decimal('0.28000000000000002665')"),
            'value': ''
        },
        {
            'category__tag_id': '3',
            'data_type': 1,
            'draft_entry__excerpt': 'sample excerpt 102',
            'is_selected': False,
            'model_version__model__model_id': 'all_tags_model',
            'prediction': GenericRepr("Decimal('0E-20')"),
            'tag__tag_id': '318',
            'threshold': GenericRepr("Decimal('0.13000000000000000444')"),
            'value': ''
        },
        {
            'category__tag_id': '4',
            'data_type': 1,
            'draft_entry__excerpt': 'sample excerpt 102',
            'is_selected': False,
            'model_version__model__model_id': 'all_tags_model',
            'prediction': GenericRepr("Decimal('0.00100000000000000002')"),
            'tag__tag_id': '401',
            'threshold': GenericRepr("Decimal('0.28999999999999998002')"),
            'value': ''
        },
        {
            'category__tag_id': '4',
            'data_type': 1,
            'draft_entry__excerpt': 'sample excerpt 102',
            'is_selected': False,
            'model_version__model__model_id': 'all_tags_model',
            'prediction': GenericRepr("Decimal('0.00100000000000000002')"),
            'tag__tag_id': '402',
            'threshold': GenericRepr("Decimal('0.45000000000000001110')"),
            'value': ''
        },
        {
            'category__tag_id': '4',
            'data_type': 1,
            'draft_entry__excerpt': 'sample excerpt 102',
            'is_selected': False,
            'model_version__model__model_id': 'all_tags_model',
            'prediction': GenericRepr("Decimal('0E-20')"),
            'tag__tag_id': '407',
            'threshold': GenericRepr("Decimal('0.07000000000000000666')"),
            'value': ''
        },
        {
            'category__tag_id': '4',
            'data_type': 1,
            'draft_entry__excerpt': 'sample excerpt 102',
            'is_selected': False,
            'model_version__model__model_id': 'all_tags_model',
            'prediction': GenericRepr("Decimal('0.00100000000000000002')"),
            'tag__tag_id': '408',
            'threshold': GenericRepr("Decimal('0.11000000000000000056')"),
            'value': ''
        },
        {
            'category__tag_id': '4',
            'data_type': 1,
            'draft_entry__excerpt': 'sample excerpt 102',
            'is_selected': False,
            'model_version__model__model_id': 'all_tags_model',
            'prediction': GenericRepr("Decimal('0E-20')"),
            'tag__tag_id': '412',
            'threshold': GenericRepr("Decimal('0.35999999999999998668')"),
            'value': ''
        },
        {
            'category__tag_id': '5',
            'data_type': 1,
            'draft_entry__excerpt': 'sample excerpt 102',
            'is_selected': False,
            'model_version__model__model_id': 'all_tags_model',
            'prediction': GenericRepr("Decimal('0E-20')"),
            'tag__tag_id': '501',
            'threshold': GenericRepr("Decimal('0.45000000000000001110')"),
            'value': ''
        },
        {
            'category__tag_id': '5',
            'data_type': 1,
            'draft_entry__excerpt': 'sample excerpt 102',
            'is_selected': False,
            'model_version__model__model_id': 'all_tags_model',
            'prediction': GenericRepr("Decimal('0E-20')"),
            'tag__tag_id': '502',
            'threshold': GenericRepr("Decimal('0.47999999999999998224')"),
            'value': ''
        },
        {
            'category__tag_id': '6',
            'data_type': 1,
            'draft_entry__excerpt': 'sample excerpt 102',
            'is_selected': False,
            'model_version__model__model_id': 'all_tags_model',
            'prediction': GenericRepr("Decimal('0E-20')"),
            'tag__tag_id': '601',
            'threshold': GenericRepr("Decimal('0.05999999999999999778')"),
            'value': ''
        },
        {
            'category__tag_id': '6',
            'data_type': 1,
            'draft_entry__excerpt': 'sample excerpt 102',
            'is_selected': False,
            'model_version__model__model_id': 'all_tags_model',
            'prediction': GenericRepr("Decimal('0.00100000000000000002')"),
            'tag__tag_id': '602',
            'threshold': GenericRepr("Decimal('0.47999999999999998224')"),
            'value': ''
        },
        {
            'category__tag_id': '6',
            'data_type': 1,
            'draft_entry__excerpt': 'sample excerpt 102',
            'is_selected': False,
            'model_version__model__model_id': 'all_tags_model',
            'prediction': GenericRepr("Decimal('0.02199999999999999872')"),
            'tag__tag_id': '603',
            'threshold': GenericRepr("Decimal('0.34000000000000002442')"),
            'value': ''
        },
        {
            'category__tag_id': '6',
            'data_type': 1,
            'draft_entry__excerpt': 'sample excerpt 102',
            'is_selected': False,
            'model_version__model__model_id': 'all_tags_model',
            'prediction': GenericRepr("Decimal('0E-20')"),
            'tag__tag_id': '604',
            'threshold': GenericRepr("Decimal('0.16000000000000000333')"),
            'value': ''
        },
        {
            'category__tag_id': '7',
            'data_type': 1,
            'draft_entry__excerpt': 'sample excerpt 102',
            'is_selected': False,
            'model_version__model__model_id': 'all_tags_model',
            'prediction': GenericRepr("Decimal('0.00800000000000000017')"),
            'tag__tag_id': '701',
            'threshold': GenericRepr("Decimal('0.27000000000000001776')"),
            'value': ''
        },
        {
            'category__tag_id': '8',
            'data_type': 1,
            'draft_entry__excerpt': 'sample excerpt 102',
            'is_selected': False,
            'model_version__model__model_id': 'all_tags_model',
            'prediction': GenericRepr("Decimal('0E-20')"),
            'tag__tag_id': '801',
            'threshold': GenericRepr("Decimal('0.66000000000000003109')"),
            'value': ''
        },
        {
            'category__tag_id': '8',
            'data_type': 1,
            'draft_entry__excerpt': 'sample excerpt 102',
            'is_selected': False,
            'model_version__model__model_id': 'all_tags_model',
            'prediction': GenericRepr("Decimal('0E-20')"),
            'tag__tag_id': '802',
            'threshold': GenericRepr("Decimal('0.29999999999999998890')"),
            'value': ''
        },
        {
            'category__tag_id': '9',
            'data_type': 1,
            'draft_entry__excerpt': 'sample excerpt 102',
            'is_selected': False,
            'model_version__model__model_id': 'all_tags_model',
            'prediction': GenericRepr("Decimal('-1.00000000000000000000')"),
            'tag__tag_id': '904',
            'threshold': GenericRepr("Decimal('-1.00000000000000000000')"),
            'value': ''
        },
        {
            'category__tag_id': '9',
            'data_type': 1,
            'draft_entry__excerpt': 'sample excerpt 102',
            'is_selected': False,
            'model_version__model__model_id': 'all_tags_model',
            'prediction': GenericRepr("Decimal('-1.00000000000000000000')"),
            'tag__tag_id': '905',
            'threshold': GenericRepr("Decimal('-1.00000000000000000000')"),
            'value': ''
        },
        {
            'category__tag_id': '9',
            'data_type': 1,
            'draft_entry__excerpt': 'sample excerpt 102',
            'is_selected': False,
            'model_version__model__model_id': 'all_tags_model',
            'prediction': GenericRepr("Decimal('-1.00000000000000000000')"),
            'tag__tag_id': '907',
            'threshold': GenericRepr("Decimal('-1.00000000000000000000')"),
            'value': ''
        }
    ]
}

snapshots['AssistedTaggingCallbackApiTest::test_tags_sync sync-tags'] = [
    {
        'group': None,
        'hide_in_analysis_framework_mapping': True,
        'is_category': True,
        'is_deprecated': False,
        'name': 'sectors',
        'parent_tag__tag_id': None,
        'tag_id': '1'
    },
    {
        'group': None,
        'hide_in_analysis_framework_mapping': True,
        'is_category': True,
        'is_deprecated': False,
        'name': 'reliability',
        'parent_tag__tag_id': None,
        'tag_id': '10'
    },
    {
        'group': 'Reliability',
        'hide_in_analysis_framework_mapping': False,
        'is_category': False,
        'is_deprecated': False,
        'name': 'Completely reliable',
        'parent_tag__tag_id': '10',
        'tag_id': '1001'
    },
    {
        'group': 'Reliability',
        'hide_in_analysis_framework_mapping': False,
        'is_category': False,
        'is_deprecated': False,
        'name': 'Usually reliable',
        'parent_tag__tag_id': '10',
        'tag_id': '1002'
    },
    {
        'group': 'Reliability',
        'hide_in_analysis_framework_mapping': False,
        'is_category': False,
        'is_deprecated': False,
        'name': 'Fairly Reliable',
        'parent_tag__tag_id': '10',
        'tag_id': '1003'
    },
    {
        'group': 'Reliability',
        'hide_in_analysis_framework_mapping': False,
        'is_category': False,
        'is_deprecated': False,
        'name': 'Unreliable',
        'parent_tag__tag_id': '10',
        'tag_id': '1004'
    },
    {
        'group': 'Sectors',
        'hide_in_analysis_framework_mapping': False,
        'is_category': False,
        'is_deprecated': False,
        'name': 'Agriculture',
        'parent_tag__tag_id': '1',
        'tag_id': '101'
    },
    {
        'group': 'Sectors',
        'hide_in_analysis_framework_mapping': False,
        'is_category': False,
        'is_deprecated': False,
        'name': 'Cross',
        'parent_tag__tag_id': '1',
        'tag_id': '102'
    },
    {
        'group': 'Sectors',
        'hide_in_analysis_framework_mapping': False,
        'is_category': False,
        'is_deprecated': False,
        'name': 'Education',
        'parent_tag__tag_id': '1',
        'tag_id': '103'
    },
    {
        'group': 'Sectors',
        'hide_in_analysis_framework_mapping': False,
        'is_category': False,
        'is_deprecated': False,
        'name': 'Food Security',
        'parent_tag__tag_id': '1',
        'tag_id': '104'
    },
    {
        'group': None,
        'hide_in_analysis_framework_mapping': True,
        'is_category': True,
        'is_deprecated': False,
        'name': 'subpillars_1d',
        'parent_tag__tag_id': None,
        'tag_id': '2'
    },
    {
        'group': 'Context',
        'hide_in_analysis_framework_mapping': False,
        'is_category': False,
        'is_deprecated': False,
        'name': 'Environment',
        'parent_tag__tag_id': '2',
        'tag_id': '201'
    },
    {
        'group': 'Context',
        'hide_in_analysis_framework_mapping': False,
        'is_category': False,
        'is_deprecated': False,
        'name': 'Socio Cultural',
        'parent_tag__tag_id': '2',
        'tag_id': '202'
    },
    {
        'group': 'Context',
        'hide_in_analysis_framework_mapping': False,
        'is_category': False,
        'is_deprecated': False,
        'name': 'Economy',
        'parent_tag__tag_id': '2',
        'tag_id': '203'
    },
    {
        'group': 'Context',
        'hide_in_analysis_framework_mapping': False,
        'is_category': False,
        'is_deprecated': False,
        'name': 'Demography',
        'parent_tag__tag_id': '2',
        'tag_id': '204'
    },
    {
        'group': 'Context',
        'hide_in_analysis_framework_mapping': False,
        'is_category': False,
        'is_deprecated': False,
        'name': 'Legal & Policy',
        'parent_tag__tag_id': '2',
        'tag_id': '205'
    },
    {
        'group': 'Context',
        'hide_in_analysis_framework_mapping': False,
        'is_category': False,
        'is_deprecated': False,
        'name': 'Security & Stability',
        'parent_tag__tag_id': '2',
        'tag_id': '206'
    },
    {
        'group': 'Context',
        'hide_in_analysis_framework_mapping': False,
        'is_category': False,
        'is_deprecated': False,
        'name': 'Politics',
        'parent_tag__tag_id': '2',
        'tag_id': '207'
    },
    {
        'group': 'Shock/Event',
        'hide_in_analysis_framework_mapping': False,
        'is_category': False,
        'is_deprecated': False,
        'name': 'Type And Characteristics',
        'parent_tag__tag_id': '2',
        'tag_id': '208'
    },
    {
        'group': 'Shock/Event',
        'hide_in_analysis_framework_mapping': False,
        'is_category': False,
        'is_deprecated': False,
        'name': 'Underlying/Aggravating Factors',
        'parent_tag__tag_id': '2',
        'tag_id': '209'
    },
    {
        'group': 'Shock/Event',
        'hide_in_analysis_framework_mapping': False,
        'is_category': False,
        'is_deprecated': False,
        'name': 'Hazard & Threats',
        'parent_tag__tag_id': '2',
        'tag_id': '210'
    },
    {
        'group': 'Displacement',
        'hide_in_analysis_framework_mapping': False,
        'is_category': False,
        'is_deprecated': False,
        'name': 'Type/Numbers/Movements',
        'parent_tag__tag_id': '2',
        'tag_id': '212'
    },
    {
        'group': 'Displacement',
        'hide_in_analysis_framework_mapping': False,
        'is_category': False,
        'is_deprecated': False,
        'name': 'Push Factors',
        'parent_tag__tag_id': '2',
        'tag_id': '213'
    },
    {
        'group': 'Displacement',
        'hide_in_analysis_framework_mapping': False,
        'is_category': False,
        'is_deprecated': False,
        'name': 'Pull Factors',
        'parent_tag__tag_id': '2',
        'tag_id': '214'
    },
    {
        'group': 'Displacement',
        'hide_in_analysis_framework_mapping': False,
        'is_category': False,
        'is_deprecated': False,
        'name': 'Intentions',
        'parent_tag__tag_id': '2',
        'tag_id': '215'
    },
    {
        'group': 'Displacement',
        'hide_in_analysis_framework_mapping': False,
        'is_category': False,
        'is_deprecated': False,
        'name': 'Local Integration',
        'parent_tag__tag_id': '2',
        'tag_id': '216'
    },
    {
        'group': 'Casualties',
        'hide_in_analysis_framework_mapping': False,
        'is_category': False,
        'is_deprecated': False,
        'name': 'Injured',
        'parent_tag__tag_id': '2',
        'tag_id': '217'
    },
    {
        'group': 'Casualties',
        'hide_in_analysis_framework_mapping': False,
        'is_category': False,
        'is_deprecated': False,
        'name': 'Missing',
        'parent_tag__tag_id': '2',
        'tag_id': '218'
    },
    {
        'group': 'Casualties',
        'hide_in_analysis_framework_mapping': False,
        'is_category': False,
        'is_deprecated': False,
        'name': 'Dead',
        'parent_tag__tag_id': '2',
        'tag_id': '219'
    },
    {
        'group': 'Humanitarian Access',
        'hide_in_analysis_framework_mapping': False,
        'is_category': False,
        'is_deprecated': False,
        'name': 'Relief To Population',
        'parent_tag__tag_id': '2',
        'tag_id': '220'
    },
    {
        'group': 'Humanitarian Access',
        'hide_in_analysis_framework_mapping': False,
        'is_category': False,
        'is_deprecated': False,
        'name': 'Population To Relief',
        'parent_tag__tag_id': '2',
        'tag_id': '221'
    },
    {
        'group': 'Humanitarian Access',
        'hide_in_analysis_framework_mapping': False,
        'is_category': False,
        'is_deprecated': False,
        'name': 'Physical Constraints',
        'parent_tag__tag_id': '2',
        'tag_id': '222'
    },
    {
        'group': 'Humanitarian Access',
        'hide_in_analysis_framework_mapping': False,
        'is_category': False,
        'is_deprecated': False,
        'name': 'Number Of People Facing Humanitarian Access Constraints/Humanitarian Access Gaps',
        'parent_tag__tag_id': '2',
        'tag_id': '223'
    },
    {
        'group': 'Information And Communication',
        'hide_in_analysis_framework_mapping': False,
        'is_category': False,
        'is_deprecated': False,
        'name': 'Communication Means And Preferences',
        'parent_tag__tag_id': '2',
        'tag_id': '224'
    },
    {
        'group': 'Information And Communication',
        'hide_in_analysis_framework_mapping': False,
        'is_category': False,
        'is_deprecated': False,
        'name': 'Information Challenges And Barriers',
        'parent_tag__tag_id': '2',
        'tag_id': '225'
    },
    {
        'group': 'Information And Communication',
        'hide_in_analysis_framework_mapping': False,
        'is_category': False,
        'is_deprecated': False,
        'name': 'Knowledge And Info Gaps (Pop)',
        'parent_tag__tag_id': '2',
        'tag_id': '226'
    },
    {
        'group': 'Information And Communication',
        'hide_in_analysis_framework_mapping': False,
        'is_category': False,
        'is_deprecated': False,
        'name': 'Knowledge And Info Gaps (Hum)',
        'parent_tag__tag_id': '2',
        'tag_id': '227'
    },
    {
        'group': 'Covid-19',
        'hide_in_analysis_framework_mapping': False,
        'is_category': False,
        'is_deprecated': False,
        'name': 'Cases',
        'parent_tag__tag_id': '2',
        'tag_id': '228'
    },
    {
        'group': 'Covid-19',
        'hide_in_analysis_framework_mapping': False,
        'is_category': False,
        'is_deprecated': False,
        'name': 'Contact Tracing',
        'parent_tag__tag_id': '2',
        'tag_id': '229'
    },
    {
        'group': 'Covid-19',
        'hide_in_analysis_framework_mapping': False,
        'is_category': False,
        'is_deprecated': False,
        'name': 'Deaths',
        'parent_tag__tag_id': '2',
        'tag_id': '230'
    },
    {
        'group': 'Covid-19',
        'hide_in_analysis_framework_mapping': False,
        'is_category': False,
        'is_deprecated': False,
        'name': 'Hospitalization & Care',
        'parent_tag__tag_id': '2',
        'tag_id': '231'
    },
    {
        'group': 'Covid-19',
        'hide_in_analysis_framework_mapping': False,
        'is_category': False,
        'is_deprecated': False,
        'name': 'Restriction Measures',
        'parent_tag__tag_id': '2',
        'tag_id': '232'
    },
    {
        'group': 'Covid-19',
        'hide_in_analysis_framework_mapping': False,
        'is_category': False,
        'is_deprecated': False,
        'name': 'Testing',
        'parent_tag__tag_id': '2',
        'tag_id': '233'
    },
    {
        'group': 'Covid-19',
        'hide_in_analysis_framework_mapping': False,
        'is_category': False,
        'is_deprecated': False,
        'name': 'Vaccination',
        'parent_tag__tag_id': '2',
        'tag_id': '234'
    },
    {
        'group': None,
        'hide_in_analysis_framework_mapping': True,
        'is_category': True,
        'is_deprecated': False,
        'name': 'subpillars_2d',
        'parent_tag__tag_id': None,
        'tag_id': '3'
    },
    {
        'group': 'At Risk',
        'hide_in_analysis_framework_mapping': False,
        'is_category': False,
        'is_deprecated': False,
        'name': 'Number Of People At Risk',
        'parent_tag__tag_id': '3',
        'tag_id': '301'
    },
    {
        'group': 'At Risk',
        'hide_in_analysis_framework_mapping': False,
        'is_category': False,
        'is_deprecated': False,
        'name': 'Risk And Vulnerabilities',
        'parent_tag__tag_id': '3',
        'tag_id': '302'
    },
    {
        'group': 'Capacities & Response',
        'hide_in_analysis_framework_mapping': False,
        'is_category': False,
        'is_deprecated': False,
        'name': 'International Response',
        'parent_tag__tag_id': '3',
        'tag_id': '303'
    },
    {
        'group': 'Capacities & Response',
        'hide_in_analysis_framework_mapping': False,
        'is_category': False,
        'is_deprecated': False,
        'name': 'Local Response',
        'parent_tag__tag_id': '3',
        'tag_id': '304'
    },
    {
        'group': 'Capacities & Response',
        'hide_in_analysis_framework_mapping': False,
        'is_category': False,
        'is_deprecated': False,
        'name': 'National Response',
        'parent_tag__tag_id': '3',
        'tag_id': '305'
    },
    {
        'group': 'Capacities & Response',
        'hide_in_analysis_framework_mapping': False,
        'is_category': False,
        'is_deprecated': False,
        'name': 'Number Of People Reached/Response Gaps',
        'parent_tag__tag_id': '3',
        'tag_id': '306'
    },
    {
        'group': 'Humanitarian Conditions',
        'hide_in_analysis_framework_mapping': False,
        'is_category': False,
        'is_deprecated': False,
        'name': 'Coping Mechanisms',
        'parent_tag__tag_id': '3',
        'tag_id': '307'
    },
    {
        'group': 'Humanitarian Conditions',
        'hide_in_analysis_framework_mapping': False,
        'is_category': False,
        'is_deprecated': False,
        'name': 'Living Standards',
        'parent_tag__tag_id': '3',
        'tag_id': '308'
    },
    {
        'group': 'Humanitarian Conditions',
        'hide_in_analysis_framework_mapping': False,
        'is_category': False,
        'is_deprecated': False,
        'name': 'Number Of People In Need',
        'parent_tag__tag_id': '3',
        'tag_id': '309'
    },
    {
        'group': 'Humanitarian Conditions',
        'hide_in_analysis_framework_mapping': False,
        'is_category': False,
        'is_deprecated': False,
        'name': 'Physical And Mental Well Being',
        'parent_tag__tag_id': '3',
        'tag_id': '310'
    },
    {
        'group': 'Impact',
        'hide_in_analysis_framework_mapping': False,
        'is_category': False,
        'is_deprecated': False,
        'name': 'Driver/Aggravating Factors',
        'parent_tag__tag_id': '3',
        'tag_id': '311'
    },
    {
        'group': 'Impact',
        'hide_in_analysis_framework_mapping': False,
        'is_category': False,
        'is_deprecated': False,
        'name': 'Impact On People',
        'parent_tag__tag_id': '3',
        'tag_id': '312'
    },
    {
        'group': 'Impact',
        'hide_in_analysis_framework_mapping': False,
        'is_category': False,
        'is_deprecated': False,
        'name': 'Impact On Systems, Services And Networks',
        'parent_tag__tag_id': '3',
        'tag_id': '313'
    },
    {
        'group': 'Impact',
        'hide_in_analysis_framework_mapping': False,
        'is_category': False,
        'is_deprecated': False,
        'name': 'Number Of People Affected',
        'parent_tag__tag_id': '3',
        'tag_id': '314'
    },
    {
        'group': 'Priority Interventions',
        'hide_in_analysis_framework_mapping': False,
        'is_category': False,
        'is_deprecated': False,
        'name': 'Expressed By Humanitarian Staff',
        'parent_tag__tag_id': '3',
        'tag_id': '315'
    },
    {
        'group': 'Priority Interventions',
        'hide_in_analysis_framework_mapping': False,
        'is_category': False,
        'is_deprecated': False,
        'name': 'Expressed By Population',
        'parent_tag__tag_id': '3',
        'tag_id': '316'
    },
    {
        'group': 'Priority Needs',
        'hide_in_analysis_framework_mapping': False,
        'is_category': False,
        'is_deprecated': False,
        'name': 'Expressed By Humanitarian Staff',
        'parent_tag__tag_id': '3',
        'tag_id': '317'
    },
    {
        'group': 'Priority Needs',
        'hide_in_analysis_framework_mapping': False,
        'is_category': False,
        'is_deprecated': False,
        'name': 'Expressed By Population',
        'parent_tag__tag_id': '3',
        'tag_id': '318'
    },
    {
        'group': None,
        'hide_in_analysis_framework_mapping': True,
        'is_category': True,
        'is_deprecated': False,
        'name': 'specific_needs_groups',
        'parent_tag__tag_id': None,
        'tag_id': '4'
    },
    {
        'group': 'Specific Needs Group',
        'hide_in_analysis_framework_mapping': False,
        'is_category': False,
        'is_deprecated': False,
        'name': 'Child Head of Household',
        'parent_tag__tag_id': '4',
        'tag_id': '401'
    },
    {
        'group': 'Specific Needs Group',
        'hide_in_analysis_framework_mapping': False,
        'is_category': False,
        'is_deprecated': False,
        'name': 'Chronically Ill',
        'parent_tag__tag_id': '4',
        'tag_id': '402'
    },
    {
        'group': 'Specific Needs Group',
        'hide_in_analysis_framework_mapping': False,
        'is_category': False,
        'is_deprecated': False,
        'name': 'Elderly Head of Household',
        'parent_tag__tag_id': '4',
        'tag_id': '403'
    },
    {
        'group': 'Specific Needs Group',
        'hide_in_analysis_framework_mapping': False,
        'is_category': False,
        'is_deprecated': False,
        'name': 'Female Head of Household',
        'parent_tag__tag_id': '4',
        'tag_id': '404'
    },
    {
        'group': 'Specific Needs Group',
        'hide_in_analysis_framework_mapping': False,
        'is_category': False,
        'is_deprecated': False,
        'name': 'GBV survivors',
        'parent_tag__tag_id': '4',
        'tag_id': '405'
    },
    {
        'group': 'Specific Needs Group',
        'hide_in_analysis_framework_mapping': False,
        'is_category': False,
        'is_deprecated': False,
        'name': 'Indigenous people',
        'parent_tag__tag_id': '4',
        'tag_id': '406'
    },
    {
        'group': 'Specific Needs Group',
        'hide_in_analysis_framework_mapping': False,
        'is_category': False,
        'is_deprecated': False,
        'name': 'LGBTQI+',
        'parent_tag__tag_id': '4',
        'tag_id': '407'
    },
    {
        'group': 'Specific Needs Group',
        'hide_in_analysis_framework_mapping': False,
        'is_category': False,
        'is_deprecated': False,
        'name': 'Minorities',
        'parent_tag__tag_id': '4',
        'tag_id': '408'
    },
    {
        'group': 'Specific Needs Group',
        'hide_in_analysis_framework_mapping': False,
        'is_category': False,
        'is_deprecated': False,
        'name': 'Persons with Disability',
        'parent_tag__tag_id': '4',
        'tag_id': '409'
    },
    {
        'group': 'Specific Needs Group',
        'hide_in_analysis_framework_mapping': False,
        'is_category': False,
        'is_deprecated': False,
        'name': 'Pregnant or Lactating Women',
        'parent_tag__tag_id': '4',
        'tag_id': '410'
    },
    {
        'group': 'Specific Needs Group',
        'hide_in_analysis_framework_mapping': False,
        'is_category': False,
        'is_deprecated': False,
        'name': 'Single Women (including Widows)',
        'parent_tag__tag_id': '4',
        'tag_id': '411'
    },
    {
        'group': 'Specific Needs Group',
        'hide_in_analysis_framework_mapping': False,
        'is_category': False,
        'is_deprecated': False,
        'name': 'Unaccompanied or Separated Children',
        'parent_tag__tag_id': '4',
        'tag_id': '412'
    },
    {
        'group': None,
        'hide_in_analysis_framework_mapping': True,
        'is_category': True,
        'is_deprecated': False,
        'name': 'gender',
        'parent_tag__tag_id': None,
        'tag_id': '5'
    },
    {
        'group': 'Gender',
        'hide_in_analysis_framework_mapping': False,
        'is_category': False,
        'is_deprecated': False,
        'name': 'Female',
        'parent_tag__tag_id': '5',
        'tag_id': '501'
    },
    {
        'group': 'Gender',
        'hide_in_analysis_framework_mapping': False,
        'is_category': False,
        'is_deprecated': False,
        'name': 'Male',
        'parent_tag__tag_id': '5',
        'tag_id': '502'
    },
    {
        'group': None,
        'hide_in_analysis_framework_mapping': True,
        'is_category': True,
        'is_deprecated': False,
        'name': 'age',
        'parent_tag__tag_id': None,
        'tag_id': '6'
    },
    {
        'group': 'Age',
        'hide_in_analysis_framework_mapping': False,
        'is_category': False,
        'is_deprecated': False,
        'name': 'Adult (18 to 59 years old)',
        'parent_tag__tag_id': '6',
        'tag_id': '601'
    },
    {
        'group': 'Age',
        'hide_in_analysis_framework_mapping': False,
        'is_category': False,
        'is_deprecated': False,
        'name': 'Children/Youth (5 to 17 years old)',
        'parent_tag__tag_id': '6',
        'tag_id': '602'
    },
    {
        'group': 'Age',
        'hide_in_analysis_framework_mapping': False,
        'is_category': False,
        'is_deprecated': False,
        'name': 'Infants/Toddlers (<5 years old)',
        'parent_tag__tag_id': '6',
        'tag_id': '603'
    },
    {
        'group': 'Age',
        'hide_in_analysis_framework_mapping': False,
        'is_category': False,
        'is_deprecated': False,
        'name': 'Older Persons (60+ years old)',
        'parent_tag__tag_id': '6',
        'tag_id': '604'
    },
    {
        'group': None,
        'hide_in_analysis_framework_mapping': True,
        'is_category': True,
        'is_deprecated': False,
        'name': 'severity',
        'parent_tag__tag_id': None,
        'tag_id': '7'
    },
    {
        'group': 'Severity',
        'hide_in_analysis_framework_mapping': False,
        'is_category': False,
        'is_deprecated': False,
        'name': 'Critical',
        'parent_tag__tag_id': '7',
        'tag_id': '701'
    },
    {
        'group': 'Severity',
        'hide_in_analysis_framework_mapping': False,
        'is_category': False,
        'is_deprecated': False,
        'name': 'Major',
        'parent_tag__tag_id': '7',
        'tag_id': '702'
    },
    {
        'group': 'Severity',
        'hide_in_analysis_framework_mapping': False,
        'is_category': False,
        'is_deprecated': False,
        'name': 'Minor Problem',
        'parent_tag__tag_id': '7',
        'tag_id': '703'
    },
    {
        'group': 'Severity',
        'hide_in_analysis_framework_mapping': False,
        'is_category': False,
        'is_deprecated': False,
        'name': 'No problem',
        'parent_tag__tag_id': '7',
        'tag_id': '704'
    },
    {
        'group': 'Severity',
        'hide_in_analysis_framework_mapping': False,
        'is_category': False,
        'is_deprecated': False,
        'name': 'Of Concern',
        'parent_tag__tag_id': '7',
        'tag_id': '705'
    },
    {
        'group': None,
        'hide_in_analysis_framework_mapping': True,
        'is_category': True,
        'is_deprecated': False,
        'name': 'affected_groups',
        'parent_tag__tag_id': None,
        'tag_id': '8'
    },
    {
        'group': 'Affected Groups',
        'hide_in_analysis_framework_mapping': False,
        'is_category': False,
        'is_deprecated': False,
        'name': 'Asylum Seekers',
        'parent_tag__tag_id': '8',
        'tag_id': '801'
    },
    {
        'group': 'Affected Groups',
        'hide_in_analysis_framework_mapping': False,
        'is_category': False,
        'is_deprecated': False,
        'name': 'Host',
        'parent_tag__tag_id': '8',
        'tag_id': '802'
    },
    {
        'group': 'Affected Groups',
        'hide_in_analysis_framework_mapping': False,
        'is_category': False,
        'is_deprecated': False,
        'name': 'IDP',
        'parent_tag__tag_id': '8',
        'tag_id': '803'
    },
    {
        'group': 'Affected Groups',
        'hide_in_analysis_framework_mapping': False,
        'is_category': False,
        'is_deprecated': False,
        'name': 'Migrants',
        'parent_tag__tag_id': '8',
        'tag_id': '804'
    },
    {
        'group': 'Affected Groups',
        'hide_in_analysis_framework_mapping': False,
        'is_category': False,
        'is_deprecated': False,
        'name': 'Refugees',
        'parent_tag__tag_id': '8',
        'tag_id': '805'
    },
    {
        'group': 'Affected Groups',
        'hide_in_analysis_framework_mapping': False,
        'is_category': False,
        'is_deprecated': False,
        'name': 'Returnees',
        'parent_tag__tag_id': '8',
        'tag_id': '806'
    },
    {
        'group': None,
        'hide_in_analysis_framework_mapping': True,
        'is_category': True,
        'is_deprecated': False,
        'name': 'demographic_group',
        'parent_tag__tag_id': None,
        'tag_id': '9'
    },
    {
        'group': 'Demographic Groups',
        'hide_in_analysis_framework_mapping': False,
        'is_category': False,
        'is_deprecated': False,
        'name': 'Infants/Toddlers (<5 years old) ',
        'parent_tag__tag_id': '9',
        'tag_id': '901'
    },
    {
        'group': 'Demographic Groups',
        'hide_in_analysis_framework_mapping': False,
        'is_category': False,
        'is_deprecated': False,
        'name': 'Female Children/Youth (5 to 17 years old)',
        'parent_tag__tag_id': '9',
        'tag_id': '902'
    },
    {
        'group': 'Demographic Groups',
        'hide_in_analysis_framework_mapping': False,
        'is_category': False,
        'is_deprecated': False,
        'name': 'Male Children/Youth (5 to 17 years old)',
        'parent_tag__tag_id': '9',
        'tag_id': '903'
    },
    {
        'group': 'Demographic Groups',
        'hide_in_analysis_framework_mapping': False,
        'is_category': False,
        'is_deprecated': False,
        'name': 'Female Adult (18 to 59 years old)',
        'parent_tag__tag_id': '9',
        'tag_id': '904'
    },
    {
        'group': 'Demographic Groups',
        'hide_in_analysis_framework_mapping': False,
        'is_category': False,
        'is_deprecated': False,
        'name': 'Male Adult (18 to 59 years old)',
        'parent_tag__tag_id': '9',
        'tag_id': '905'
    },
    {
        'group': 'Demographic Groups',
        'hide_in_analysis_framework_mapping': False,
        'is_category': False,
        'is_deprecated': False,
        'name': 'Female Older Persons (60+ years old)',
        'parent_tag__tag_id': '9',
        'tag_id': '906'
    },
    {
        'group': 'Demographic Groups',
        'hide_in_analysis_framework_mapping': False,
        'is_category': False,
        'is_deprecated': False,
        'name': 'Male Older Persons (60+ years old)',
        'parent_tag__tag_id': '9',
        'tag_id': '907'
    }
]
