# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot


snapshots = Snapshot()

snapshots['TestLeadMutationSchema::test_unified_connector_create success'] = {
    'clientId': 'u-connector-101',
    'id': '1',
    'isActive': False,
    'project': '1',
    'sources': [
        {
            'clientId': 'connector-source-101',
            'id': '1',
            'params': {
                'sample-key': 'sample-value'
            },
            'source': 'ATOM_FEED',
            'title': 'connector-s-1',
            'unifiedConnector': '1'
        },
        {
            'clientId': 'connector-source-102',
            'id': '2',
            'params': {
                'sample-key': 'sample-value'
            },
            'source': 'RELIEF_WEB',
            'title': 'connector-s-2',
            'unifiedConnector': '1'
        }
    ],
    'title': 'unified-connector-s-1'
}

snapshots['TestLeadMutationSchema::test_unified_connector_update success-1'] = {
    'clientId': 'u-connector-101',
    'id': '1',
    'isActive': False,
    'project': '1',
    'sources': [
        {
            'clientId': 'connector-source-101',
            'id': '1',
            'params': {
            },
            'source': 'ATOM_FEED',
            'title': 'Connector-Source-0',
            'unifiedConnector': '1'
        },
        {
            'clientId': 'connector-source-102',
            'id': '2',
            'params': {
            },
            'source': 'RELIEF_WEB',
            'title': 'Connector-Source-1',
            'unifiedConnector': '1'
        },
        {
            'clientId': 'connector-source-103',
            'id': '4',
            'params': {
            },
            'source': 'RSS_FEED',
            'title': 'Connector-Source-2',
            'unifiedConnector': '1'
        }
    ],
    'title': 'Unified-Connector-0'
}
