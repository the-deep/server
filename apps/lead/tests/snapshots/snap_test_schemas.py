# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot


snapshots = Snapshot()

snapshots['TestLeadBulkMutationSchema::test_lead_bulk success'] = {
    'errors': [
        None,
        None,
        [
            {
                'arrayErrors': None,
                'clientId': 'new-lead-3',
                'field': 'nonFieldErrors',
                'messages': 'A lead with this URL has already been added to Project: Project-0',
                'objectErrors': None
            }
        ],
        None,
        None
    ],
    'result': [
        {
            'clientId': 'new-lead-1',
            'id': '3',
            'title': 'Lead title 1'
        },
        {
            'clientId': 'new-lead-2',
            'id': '4',
            'title': 'Lead title 2'
        },
        None,
        {
            'clientId': '1',
            'id': '1',
            'title': 'Lead title 3'
        },
        {
            'clientId': '2',
            'id': '2',
            'title': 'Lead title 4'
        }
    ]
}
