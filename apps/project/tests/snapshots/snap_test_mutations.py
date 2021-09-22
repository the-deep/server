# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot


snapshots = Snapshot()

snapshots['TestProjectMembershipMutation::test_user_membership_bulk try 1'] = {
    'deletedResult': [
        {
            'addedBy': {
                'displayName': 'Jeffery Wagner',
                'id': '6'
            },
            'badges': [
                'QA'
            ],
            'clientId': '1',
            'id': '1',
            'joinedAt': '2021-01-01T00:00:00.123456+00:00',
            'member': {
                'displayName': 'Jeffery Wagner',
                'id': '6'
            },
            'role': {
                'id': '6',
                'level': 200,
                'title': 'Analyst'
            }
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
                'displayName': 'Anthony Gonzalez',
                'id': '7'
            },
            'badges': [
                'QA'
            ],
            'clientId': 'member-user-2',
            'id': '2',
            'joinedAt': '2021-01-01T00:00:00.123456+00:00',
            'member': {
                'displayName': 'Anthony Gonzalez',
                'id': '7'
            },
            'role': {
                'id': '8',
                'title': 'Clairvoyant One'
            }
        },
        None,
        {
            'addedBy': {
                'displayName': 'Joshua Walker',
                'id': '2'
            },
            'badges': [
            ],
            'clientId': 'member-user-3',
            'id': '8',
            'joinedAt': '2021-01-01T00:00:00.123456+00:00',
            'member': {
                'displayName': 'Debra Gardner',
                'id': '8'
            },
            'role': {
                'id': '6',
                'title': 'Analyst'
            }
        },
        {
            'addedBy': {
                'displayName': 'Joshua Walker',
                'id': '2'
            },
            'badges': [
            ],
            'clientId': 'member-user-4',
            'id': '9',
            'joinedAt': '2021-01-01T00:00:00.123456+00:00',
            'member': {
                'displayName': 'Jeffrey Lawrence',
                'id': '9'
            },
            'role': {
                'id': '6',
                'title': 'Analyst'
            }
        }
    ]
}

snapshots['TestProjectMembershipMutation::test_user_membership_bulk try 2'] = {
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
        ],
        [
            {
                'arrayErrors': None,
                'clientId': 'member-user-2',
                'field': 'member',
                'messages': 'Changing member is not allowed!',
                'objectErrors': None
            }
        ],
        [
            {
                'arrayErrors': None,
                'clientId': 'member-user-2',
                'field': 'role',
                'messages': 'Changing same level role is not allowed!',
                'objectErrors': None
            }
        ]
    ],
    'result': [
        {
            'addedBy': {
                'displayName': 'Anthony Gonzalez',
                'id': '7'
            },
            'badges': [
                'QA'
            ],
            'clientId': 'member-user-2',
            'id': '2',
            'joinedAt': '2021-01-01T00:00:00.123456+00:00',
            'member': {
                'displayName': 'Anthony Gonzalez',
                'id': '7'
            },
            'role': {
                'id': '8',
                'title': 'Clairvoyant One'
            }
        },
        None,
        None,
        None,
        None
    ]
}
