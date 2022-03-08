# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import GenericRepr, Snapshot


snapshots = Snapshot()

snapshots['AssistedTaggingCallbackApiTest::test_save_draft_entry final-current-model-stats'] = {
    'model_count': 3,
    'model_version_count': 3,
    'model_versions': [
        {
            'model__model_id': 'all_tags_model',
            'version': '1.0.0'
        },
        {
            'model__model_id': 'reliability',
            'version': '1.0.0'
        },
        {
            'model__model_id': 'geolocations',
            'version': '1.0.0'
        }
    ],
    'models': [
        {
            'model_id': 'all_tags_model',
            'name': 'all_tags_model'
        },
        {
            'model_id': 'reliability',
            'name': 'reliability'
        },
        {
            'model_id': 'geolocations',
            'name': 'geolocations'
        }
    ],
    'tag_count': 12,
    'tags': [
        {
            'is_depricated': False,
            'name': 'category-all-tags-1',
            'tag_id': 'category-all-tags-1'
        },
        {
            'is_depricated': False,
            'name': 'tag-all-tags-1-1',
            'tag_id': 'tag-all-tags-1-1'
        },
        {
            'is_depricated': False,
            'name': 'tag-all-tags-1-2',
            'tag_id': 'tag-all-tags-1-2'
        },
        {
            'is_depricated': False,
            'name': 'category-all-tags-2',
            'tag_id': 'category-all-tags-2'
        },
        {
            'is_depricated': False,
            'name': 'tag-all-tags-2-1',
            'tag_id': 'tag-all-tags-2-1'
        },
        {
            'is_depricated': False,
            'name': 'tag-all-tags-2-2',
            'tag_id': 'tag-all-tags-2-2'
        },
        {
            'is_depricated': False,
            'name': 'category-reliability-1',
            'tag_id': 'category-reliability-1'
        },
        {
            'is_depricated': False,
            'name': 'tag-reliability-1-1',
            'tag_id': 'tag-reliability-1-1'
        },
        {
            'is_depricated': False,
            'name': 'tag-reliability-1-2',
            'tag_id': 'tag-reliability-1-2'
        },
        {
            'is_depricated': False,
            'name': 'category-reliability-2',
            'tag_id': 'category-reliability-2'
        },
        {
            'is_depricated': False,
            'name': 'tag-reliability-2-1',
            'tag_id': 'tag-reliability-2-1'
        },
        {
            'is_depricated': False,
            'name': 'tag-reliability-2-2',
            'tag_id': 'tag-reliability-2-2'
        }
    ]
}

snapshots['AssistedTaggingCallbackApiTest::test_save_draft_entry final-current-prediction-stats'] = {
    'prediction_count': 22,
    'predictions': [
        {
            'category__tag_id': None,
            'data_type': 0,
            'draft_entry__excerpt': 'sample excerpt 101',
            'is_selected': True,
            'model_version__model__model_id': 'geolocations',
            'prediction': None,
            'tag__tag_id': None,
            'threshold': None,
            'value': 'Bagmati'
        },
        {
            'category__tag_id': None,
            'data_type': 0,
            'draft_entry__excerpt': 'sample excerpt 101',
            'is_selected': True,
            'model_version__model__model_id': 'geolocations',
            'prediction': None,
            'tag__tag_id': None,
            'threshold': None,
            'value': 'Kathmandu'
        },
        {
            'category__tag_id': None,
            'data_type': 0,
            'draft_entry__excerpt': 'sample excerpt 101',
            'is_selected': True,
            'model_version__model__model_id': 'geolocations',
            'prediction': None,
            'tag__tag_id': None,
            'threshold': None,
            'value': 'Nepal'
        },
        {
            'category__tag_id': None,
            'data_type': 0,
            'draft_entry__excerpt': 'sample excerpt 102',
            'is_selected': True,
            'model_version__model__model_id': 'geolocations',
            'prediction': None,
            'tag__tag_id': None,
            'threshold': None,
            'value': 'Bagmati'
        },
        {
            'category__tag_id': None,
            'data_type': 0,
            'draft_entry__excerpt': 'sample excerpt 102',
            'is_selected': True,
            'model_version__model__model_id': 'geolocations',
            'prediction': None,
            'tag__tag_id': None,
            'threshold': None,
            'value': 'Kathmandu'
        },
        {
            'category__tag_id': None,
            'data_type': 0,
            'draft_entry__excerpt': 'sample excerpt 102',
            'is_selected': True,
            'model_version__model__model_id': 'geolocations',
            'prediction': None,
            'tag__tag_id': None,
            'threshold': None,
            'value': 'Nepal'
        },
        {
            'category__tag_id': 'category-all-tags-1',
            'data_type': 1,
            'draft_entry__excerpt': 'sample excerpt 101',
            'is_selected': False,
            'model_version__model__model_id': 'all_tags_model',
            'prediction': GenericRepr("Decimal('0.00011000000000000000')"),
            'tag__tag_id': 'tag-all-tags-1-1',
            'threshold': GenericRepr("Decimal('0.00011000000000000000')"),
            'value': ''
        },
        {
            'category__tag_id': 'category-all-tags-1',
            'data_type': 1,
            'draft_entry__excerpt': 'sample excerpt 101',
            'is_selected': False,
            'model_version__model__model_id': 'all_tags_model',
            'prediction': GenericRepr("Decimal('0.00012000000000000000')"),
            'tag__tag_id': 'tag-all-tags-1-2',
            'threshold': GenericRepr("Decimal('0.00012000000000000000')"),
            'value': ''
        },
        {
            'category__tag_id': 'category-all-tags-2',
            'data_type': 1,
            'draft_entry__excerpt': 'sample excerpt 101',
            'is_selected': True,
            'model_version__model__model_id': 'all_tags_model',
            'prediction': GenericRepr("Decimal('0.00021000000000000000')"),
            'tag__tag_id': 'tag-all-tags-2-1',
            'threshold': GenericRepr("Decimal('0.00021000000000000000')"),
            'value': ''
        },
        {
            'category__tag_id': 'category-all-tags-2',
            'data_type': 1,
            'draft_entry__excerpt': 'sample excerpt 101',
            'is_selected': True,
            'model_version__model__model_id': 'all_tags_model',
            'prediction': GenericRepr("Decimal('0.00022000000000000000')"),
            'tag__tag_id': 'tag-all-tags-2-2',
            'threshold': GenericRepr("Decimal('0.00022000000000000000')"),
            'value': ''
        },
        {
            'category__tag_id': 'category-all-tags-1',
            'data_type': 1,
            'draft_entry__excerpt': 'sample excerpt 102',
            'is_selected': False,
            'model_version__model__model_id': 'all_tags_model',
            'prediction': GenericRepr("Decimal('0.00011000000000000000')"),
            'tag__tag_id': 'tag-all-tags-1-1',
            'threshold': GenericRepr("Decimal('0.00011000000000000000')"),
            'value': ''
        },
        {
            'category__tag_id': 'category-all-tags-1',
            'data_type': 1,
            'draft_entry__excerpt': 'sample excerpt 102',
            'is_selected': False,
            'model_version__model__model_id': 'all_tags_model',
            'prediction': GenericRepr("Decimal('0.00012000000000000000')"),
            'tag__tag_id': 'tag-all-tags-1-2',
            'threshold': GenericRepr("Decimal('0.00012000000000000000')"),
            'value': ''
        },
        {
            'category__tag_id': 'category-all-tags-2',
            'data_type': 1,
            'draft_entry__excerpt': 'sample excerpt 102',
            'is_selected': True,
            'model_version__model__model_id': 'all_tags_model',
            'prediction': GenericRepr("Decimal('0.00021000000000000000')"),
            'tag__tag_id': 'tag-all-tags-2-1',
            'threshold': GenericRepr("Decimal('0.00021000000000000000')"),
            'value': ''
        },
        {
            'category__tag_id': 'category-all-tags-2',
            'data_type': 1,
            'draft_entry__excerpt': 'sample excerpt 102',
            'is_selected': True,
            'model_version__model__model_id': 'all_tags_model',
            'prediction': GenericRepr("Decimal('0.00022000000000000000')"),
            'tag__tag_id': 'tag-all-tags-2-2',
            'threshold': GenericRepr("Decimal('0.00022000000000000000')"),
            'value': ''
        },
        {
            'category__tag_id': 'category-reliability-1',
            'data_type': 1,
            'draft_entry__excerpt': 'sample excerpt 101',
            'is_selected': False,
            'model_version__model__model_id': 'reliability',
            'prediction': None,
            'tag__tag_id': 'tag-reliability-1-1',
            'threshold': None,
            'value': ''
        },
        {
            'category__tag_id': 'category-reliability-1',
            'data_type': 1,
            'draft_entry__excerpt': 'sample excerpt 101',
            'is_selected': True,
            'model_version__model__model_id': 'reliability',
            'prediction': None,
            'tag__tag_id': 'tag-reliability-1-2',
            'threshold': None,
            'value': ''
        },
        {
            'category__tag_id': 'category-reliability-2',
            'data_type': 1,
            'draft_entry__excerpt': 'sample excerpt 101',
            'is_selected': False,
            'model_version__model__model_id': 'reliability',
            'prediction': None,
            'tag__tag_id': 'tag-reliability-2-1',
            'threshold': None,
            'value': ''
        },
        {
            'category__tag_id': 'category-reliability-2',
            'data_type': 1,
            'draft_entry__excerpt': 'sample excerpt 101',
            'is_selected': True,
            'model_version__model__model_id': 'reliability',
            'prediction': None,
            'tag__tag_id': 'tag-reliability-2-2',
            'threshold': None,
            'value': ''
        },
        {
            'category__tag_id': 'category-reliability-1',
            'data_type': 1,
            'draft_entry__excerpt': 'sample excerpt 102',
            'is_selected': False,
            'model_version__model__model_id': 'reliability',
            'prediction': None,
            'tag__tag_id': 'tag-reliability-1-1',
            'threshold': None,
            'value': ''
        },
        {
            'category__tag_id': 'category-reliability-1',
            'data_type': 1,
            'draft_entry__excerpt': 'sample excerpt 102',
            'is_selected': True,
            'model_version__model__model_id': 'reliability',
            'prediction': None,
            'tag__tag_id': 'tag-reliability-1-2',
            'threshold': None,
            'value': ''
        },
        {
            'category__tag_id': 'category-reliability-2',
            'data_type': 1,
            'draft_entry__excerpt': 'sample excerpt 102',
            'is_selected': False,
            'model_version__model__model_id': 'reliability',
            'prediction': None,
            'tag__tag_id': 'tag-reliability-2-1',
            'threshold': None,
            'value': ''
        },
        {
            'category__tag_id': 'category-reliability-2',
            'data_type': 1,
            'draft_entry__excerpt': 'sample excerpt 102',
            'is_selected': True,
            'model_version__model__model_id': 'reliability',
            'prediction': None,
            'tag__tag_id': 'tag-reliability-2-2',
            'threshold': None,
            'value': ''
        }
    ]
}
