# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot


snapshots = Snapshot()

snapshots['TestUserGroupMutationSnapShotTestCase::test_usergroup_membership_bulk try 1'] = {
    'deletedResult': [
        {
            'addedBy': {
                'displayName': 'Robert Johnson',
                'id': '5'
            },
            'clientId': '1',
            'id': '1',
            'joinedAt': '2021-01-01T00:00:00.123456+00:00',
            'member': {
                'displayName': 'Robert Johnson',
                'id': '5'
            },
            'role': 'NORMAL'
        }
    ],
    'errors': [
        None,
        [
            {
                'arrayErrors': None,
                'clientId': 'member-user-5',
                'field': 'member',
                'messages': 'User is already a member!',
                'objectErrors': None
            }
        ],
        None,
        None
    ],
    'result': [
        {
            'addedBy': {
                'displayName': 'Jeffery Wagner',
                'id': '6'
            },
            'clientId': 'member-user-2',
            'id': '2',
            'joinedAt': '2021-01-01T00:00:00.123456+00:00',
            'member': {
                'displayName': 'Jeffery Wagner',
                'id': '6'
            },
            'role': 'ADMIN'
        },
        None,
        {
            'addedBy': {
                'displayName': 'Joshua Walker',
                'id': '2'
            },
            'clientId': 'member-user-3',
            'id': '7',
            'joinedAt': '2021-01-01T00:00:00.123456+00:00',
            'member': {
                'displayName': 'Anthony Gonzalez',
                'id': '7'
            },
            'role': 'NORMAL'
        },
        {
            'addedBy': {
                'displayName': 'Joshua Walker',
                'id': '2'
            },
            'clientId': 'member-user-4',
            'id': '8',
            'joinedAt': '2021-01-01T00:00:00.123456+00:00',
            'member': {
                'displayName': 'Debra Gardner',
                'id': '8'
            },
            'role': 'NORMAL'
        }
    ]
}

snapshots['TestUserGroupMutationSnapShotTestCase::test_usergroup_membership_bulk try 2'] = {
    'deletedResult': [
    ],
    'errors': [
        None,
        [
            {
                'arrayErrors': None,
                'clientId': 'member-user-3',
                'field': 'member',
                'messages': 'User is already a member!',
                'objectErrors': None
            }
        ],
        [
            {
                'arrayErrors': None,
                'clientId': 'member-user-4',
                'field': 'member',
                'messages': 'User is already a member!',
                'objectErrors': None
            }
        ]
    ],
    'result': [
        {
            'addedBy': {
                'displayName': 'Jeffery Wagner',
                'id': '6'
            },
            'clientId': 'member-user-2',
            'id': '2',
            'joinedAt': '2021-01-01T00:00:00.123456+00:00',
            'member': {
                'displayName': 'Jeffery Wagner',
                'id': '6'
            },
            'role': 'ADMIN'
        },
        None,
        None
    ]
}
