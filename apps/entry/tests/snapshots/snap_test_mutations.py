# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot


snapshots = Snapshot()

snapshots['TestEntryMutation::test_entry_create error'] = {
    'data': {
        'project': {
            'entryCreate': {
                'errors': [
                    {
                        'arrayErrors': None,
                        'clientId': 'entry-101',
                        'field': 'image',
                        'messages': "You don't have permission to attach image: file-1",
                        'objectErrors': None
                    }
                ],
                'ok': False,
                'result': None
            }
        }
    }
}

snapshots['TestEntryMutation::test_entry_create success'] = {
    'data': {
        'project': {
            'entryCreate': {
                'errors': None,
                'ok': True,
                'result': {
                    'attributes': [
                        {
                            'clientId': 'client-id-attribute-1',
                            'data': {
                            },
                            'id': '1',
                            'widget': '1',
                            'widgetType': 'TIME_RANGE'
                        },
                        {
                            'clientId': 'client-id-attribute-2',
                            'data': {
                            },
                            'id': '2',
                            'widget': '2',
                            'widgetType': 'TIME'
                        },
                        {
                            'clientId': 'client-id-attribute-3',
                            'data': {
                            },
                            'id': '3',
                            'widget': '3',
                            'widgetType': 'GEO'
                        }
                    ],
                    'clientId': 'entry-101',
                    'droppedExcerpt': 'This is a dropped text',
                    'entryType': 'EXCERPT',
                    'excerpt': 'This is a text',
                    'highlightHidden': False,
                    'id': '1',
                    'image': {
                        'id': '3',
                        'title': 'file-2'
                    },
                    'informationDate': '2021-01-01',
                    'order': 1
                }
            }
        }
    }
}
