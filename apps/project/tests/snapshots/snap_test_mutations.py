# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot


snapshots = Snapshot()

snapshots['TestProjectMembershipMutation::test_user_group_membership_admin_bulk try 1'] = {
    'deletedResult': [
        {
            'addedBy': None,
            'badges': [
                'QA'
            ],
            'clientId': '1',
            'id': '1',
            'joinedAt': '2021-01-01T00:00:00.123456+00:00',
            'role': {
                'id': '6',
                'level': 200,
                'title': 'Analyst'
            },
            'usergroup': {
                'id': '3',
                'title': 'Group-2'
            }
        }
    ],
    'errors': [
        [
            {
                'arrayErrors': None,
                'clientId': 'member-user-2',
                'field': 'role',
                'messages': 'Access is denied for higher role assignment.',
                'objectErrors': None
            }
        ],
        [
            {
                'arrayErrors': None,
                'clientId': 'member-user-5',
                'field': 'usergroup',
                'messages': 'UserGroup already a member!',
                'objectErrors': None
            }
        ],
        None,
        None
    ],
    'result': [
        None,
        None,
        {
            'addedBy': {
                'displayName': 'Danielle Johnson',
                'id': '1'
            },
            'badges': [
            ],
            'clientId': 'member-user-3',
            'id': '6',
            'joinedAt': '2021-01-01T00:00:00.123456+00:00',
            'role': {
                'id': '6',
                'title': 'Analyst'
            },
            'usergroup': {
                'id': '5',
                'title': 'Group-4'
            }
        },
        {
            'addedBy': {
                'displayName': 'Danielle Johnson',
                'id': '1'
            },
            'badges': [
            ],
            'clientId': 'member-user-4',
            'id': '7',
            'joinedAt': '2021-01-01T00:00:00.123456+00:00',
            'role': {
                'id': '6',
                'title': 'Analyst'
            },
            'usergroup': {
                'id': '6',
                'title': 'Group-5'
            }
        }
    ]
}

snapshots['TestProjectMembershipMutation::test_user_group_membership_admin_bulk try 2'] = {
    'deletedResult': [
    ],
    'errors': [
        [
            {
                'arrayErrors': None,
                'clientId': 'member-user-2',
                'field': 'role',
                'messages': 'Access is denied for higher role assignment.',
                'objectErrors': None
            }
        ],
        [
            {
                'arrayErrors': None,
                'clientId': 'member-user-3',
                'field': 'usergroup',
                'messages': 'UserGroup already a member!',
                'objectErrors': None
            }
        ],
        [
            {
                'arrayErrors': None,
                'clientId': 'member-user-4',
                'field': 'usergroup',
                'messages': 'UserGroup already a member!',
                'objectErrors': None
            }
        ],
        [
            {
                'arrayErrors': None,
                'clientId': 'member-user-2',
                'field': 'usergroup',
                'messages': 'Changing usergroup is not allowed!',
                'objectErrors': None
            },
            {
                'arrayErrors': None,
                'clientId': 'member-user-2',
                'field': 'role',
                'messages': 'Access is denied for higher role assignment.',
                'objectErrors': None
            }
        ],
        None
    ],
    'result': [
        None,
        None,
        None,
        None,
        {
            'addedBy': None,
            'badges': [
            ],
            'clientId': 'member-user-2',
            'id': '2',
            'joinedAt': '2021-01-01T00:00:00.123456+00:00',
            'role': {
                'id': '7',
                'title': 'Admin'
            },
            'usergroup': {
                'id': '4',
                'title': 'Group-3'
            }
        }
    ]
}

snapshots['TestProjectMembershipMutation::test_user_group_membership_using_clairvoyan_one_bulk try 1'] = {
    'deletedResult': [
        {
            'addedBy': None,
            'badges': [
                'QA'
            ],
            'clientId': '1',
            'id': '1',
            'joinedAt': '2021-01-01T00:00:00.123456+00:00',
            'role': {
                'id': '6',
                'level': 200,
                'title': 'Analyst'
            },
            'usergroup': {
                'id': '3',
                'title': 'Group-10'
            }
        }
    ],
    'errors': [
        None,
        [
            {
                'arrayErrors': None,
                'clientId': 'member-user-5',
                'field': 'usergroup',
                'messages': 'UserGroup already a member!',
                'objectErrors': None
            }
        ],
        None,
        None
    ],
    'result': [
        {
            'addedBy': None,
            'badges': [
                'QA'
            ],
            'clientId': 'member-user-2',
            'id': '2',
            'joinedAt': '2021-01-01T00:00:00.123456+00:00',
            'role': {
                'id': '8',
                'title': 'Clairvoyant One'
            },
            'usergroup': {
                'id': '4',
                'title': 'Group-11'
            }
        },
        None,
        {
            'addedBy': {
                'displayName': 'Danielle Johnson',
                'id': '1'
            },
            'badges': [
            ],
            'clientId': 'member-user-3',
            'id': '6',
            'joinedAt': '2021-01-01T00:00:00.123456+00:00',
            'role': {
                'id': '6',
                'title': 'Analyst'
            },
            'usergroup': {
                'id': '5',
                'title': 'Group-12'
            }
        },
        {
            'addedBy': {
                'displayName': 'Danielle Johnson',
                'id': '1'
            },
            'badges': [
            ],
            'clientId': 'member-user-4',
            'id': '7',
            'joinedAt': '2021-01-01T00:00:00.123456+00:00',
            'role': {
                'id': '6',
                'title': 'Analyst'
            },
            'usergroup': {
                'id': '6',
                'title': 'Group-13'
            }
        }
    ]
}

snapshots['TestProjectMembershipMutation::test_user_group_membership_using_clairvoyan_one_bulk try 2'] = {
    'deletedResult': [
    ],
    'errors': [
        None,
        [
            {
                'arrayErrors': None,
                'clientId': 'member-user-3',
                'field': 'usergroup',
                'messages': 'UserGroup already a member!',
                'objectErrors': None
            }
        ],
        [
            {
                'arrayErrors': None,
                'clientId': 'member-user-4',
                'field': 'usergroup',
                'messages': 'UserGroup already a member!',
                'objectErrors': None
            }
        ],
        [
            {
                'arrayErrors': None,
                'clientId': 'member-user-2',
                'field': 'usergroup',
                'messages': 'Changing usergroup is not allowed!',
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
            'addedBy': None,
            'badges': [
                'QA'
            ],
            'clientId': 'member-user-2',
            'id': '2',
            'joinedAt': '2021-01-01T00:00:00.123456+00:00',
            'role': {
                'id': '8',
                'title': 'Clairvoyant One'
            },
            'usergroup': {
                'id': '4',
                'title': 'Group-11'
            }
        },
        None,
        None,
        None,
        None
    ]
}

snapshots['TestProjectMembershipMutation::test_user_membership_admin_bulk try 1'] = {
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
        [
            {
                'arrayErrors': None,
                'clientId': 'member-user-2',
                'field': 'role',
                'messages': 'Access is denied for higher role assignment.',
                'objectErrors': None
            }
        ],
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
        None,
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

snapshots['TestProjectMembershipMutation::test_user_membership_admin_bulk try 2'] = {
    'deletedResult': [
    ],
    'errors': [
        [
            {
                'arrayErrors': None,
                'clientId': 'member-user-2',
                'field': 'role',
                'messages': 'Access is denied for higher role assignment.',
                'objectErrors': None
            }
        ],
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
            },
            {
                'arrayErrors': None,
                'clientId': 'member-user-2',
                'field': 'role',
                'messages': 'Access is denied for higher role assignment.',
                'objectErrors': None
            }
        ],
        None
    ],
    'result': [
        None,
        None,
        None,
        None,
        {
            'addedBy': {
                'displayName': 'Anthony Gonzalez',
                'id': '7'
            },
            'badges': [
            ],
            'clientId': 'member-user-2',
            'id': '2',
            'joinedAt': '2021-01-01T00:00:00.123456+00:00',
            'member': {
                'displayName': 'Anthony Gonzalez',
                'id': '7'
            },
            'role': {
                'id': '7',
                'title': 'Admin'
            }
        }
    ]
}

snapshots['TestProjectMembershipMutation::test_user_membership_using_clairvoyan_one_bulk try 1'] = {
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

snapshots['TestProjectMembershipMutation::test_user_membership_using_clairvoyan_one_bulk try 2'] = {
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
