# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot


snapshots = Snapshot()

snapshots['ProjectMutationSnapshotTest::test_project_create_mutation private-af-private-project-success'] = {
    'errors': None,
    'ok': True,
    'result': {
        'analysisFramework': {
            'id': '3',
            'isPrivate': True
        },
        'description': 'Project description 101',
        'endDate': '2021-01-01',
        'hasPubliclyViewableUnprotectedLeads': False,
        'hasPubliclyViewableRestrictedLeads': False,
        'hasPubliclyViewableConfidentialLeads': False,
        'id': '1',
        'isPrivate': True,
        'isVisualizationEnabled': False,
        'organizations': [
            {
                'id': '1',
                'organization': {
                    'id': '1',
                    'title': 'Organization-0'
                },
                'organizationType': 'LEAD_ORGANIZATION',
                'organizationTypeDisplay': 'Lead Organization'
            }
        ],
        'startDate': '2020-01-01',
        'status': 'ACTIVE',
        'title': 'Project 1'
    }
}

snapshots['ProjectMutationSnapshotTest::test_project_create_mutation public-af-private-project-success'] = {
    'errors': None,
    'ok': True,
    'result': {
        'analysisFramework': {
            'id': '1',
            'isPrivate': False
        },
        'description': 'Project description 101',
        'endDate': '2021-01-01',
        'hasPubliclyViewableUnprotectedLeads': False,
        'hasPubliclyViewableRestrictedLeads': False,
        'hasPubliclyViewableConfidentialLeads': False,
        'id': '2',
        'isPrivate': True,
        'isVisualizationEnabled': False,
        'organizations': [
            {
                'id': '2',
                'organization': {
                    'id': '1',
                    'title': 'Organization-0'
                },
                'organizationType': 'LEAD_ORGANIZATION',
                'organizationTypeDisplay': 'Lead Organization'
            }
        ],
        'startDate': '2020-01-01',
        'status': 'ACTIVE',
        'title': 'Project 2'
    }
}

snapshots['ProjectMutationSnapshotTest::test_project_create_mutation public-af-public-project-success'] = {
    'errors': None,
    'ok': True,
    'result': {
        'analysisFramework': {
            'id': '1',
            'isPrivate': False
        },
        'description': 'Project description 101',
        'endDate': '2021-01-01',
        'hasPubliclyViewableUnprotectedLeads': False,
        'hasPubliclyViewableRestrictedLeads': False,
        'hasPubliclyViewableConfidentialLeads': False,
        'id': '3',
        'isPrivate': False,
        'isVisualizationEnabled': False,
        'organizations': [
            {
                'id': '3',
                'organization': {
                    'id': '1',
                    'title': 'Organization-0'
                },
                'organizationType': 'LEAD_ORGANIZATION',
                'organizationTypeDisplay': 'Lead Organization'
            }
        ],
        'startDate': '2020-01-01',
        'status': 'ACTIVE',
        'title': 'Project 3'
    }
}

snapshots['ProjectMutationSnapshotTest::test_project_update_mutation private-project:is-private-change-error'] = {
    'data': {
        '__typename': 'Mutation',
        'project': {
            'projectUpdate': {
                'errors': [
                    {
                        'arrayErrors': None,
                        'clientId': None,
                        'field': 'isPrivate',
                        'messages': 'Cannot change privacy of project.',
                        'objectErrors': None
                    }
                ],
                'ok': False,
                'result': None
            }
        }
    }
}

snapshots['ProjectMutationSnapshotTest::test_project_update_mutation private-project:private-af'] = {
    'data': {
        '__typename': 'Mutation',
        'project': {
            'projectUpdate': {
                'errors': [
                    {
                        'arrayErrors': None,
                        'clientId': None,
                        'field': 'analysisFramework',
                        'messages': "Either framework doesn't exists or you don't have access",
                        'objectErrors': None
                    }
                ],
                'ok': False,
                'result': None
            }
        }
    }
}

snapshots['ProjectMutationSnapshotTest::test_project_update_mutation public-project:is-private-change-error'] = {
    'data': {
        '__typename': 'Mutation',
        'project': {
            'projectUpdate': {
                'errors': [
                    {
                        'arrayErrors': None,
                        'clientId': None,
                        'field': 'isPrivate',
                        'messages': 'Cannot change privacy of project.',
                        'objectErrors': None
                    }
                ],
                'ok': False,
                'result': None
            }
        }
    }
}

snapshots['ProjectMutationSnapshotTest::test_project_update_mutation public-project:private-af'] = {
    'data': {
        '__typename': 'Mutation',
        'project': {
            'projectUpdate': {
                'errors': [
                    {
                        'arrayErrors': None,
                        'clientId': None,
                        'field': 'analysisFramework',
                        'messages': "Either framework doesn't exists or you don't have access",
                        'objectErrors': None
                    }
                ],
                'ok': False,
                'result': None
            }
        }
    }
}

snapshots['ProjectMutationSnapshotTest::test_project_update_mutation public-project:private-af-with-membership'] = {
    'data': {
        '__typename': 'Mutation',
        'project': {
            'projectUpdate': {
                'errors': [
                    {
                        'arrayErrors': None,
                        'clientId': None,
                        'field': 'analysisFramework',
                        'messages': 'Cannot use private framework in public project',
                        'objectErrors': None
                    }
                ],
                'ok': False,
                'result': None
            }
        }
    }
}

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
                'id': '3',
                'level': 200,
                'title': 'Member'
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
                'profile': {
                    'displayName': 'Danielle Johnson',
                },
                'id': '1'
            },
            'badges': [
            ],
            'clientId': 'member-user-3',
            'id': '6',
            'joinedAt': '2021-01-01T00:00:00.123456+00:00',
            'role': {
                'id': '3',
                'title': 'Member'
            },
            'usergroup': {
                'id': '5',
                'title': 'Group-4'
            }
        },
        {
            'addedBy': {
                'profile': {
                    'displayName': 'Danielle Johnson',
                },
                'id': '1'
            },
            'badges': [
            ],
            'clientId': 'member-user-4',
            'id': '7',
            'joinedAt': '2021-01-01T00:00:00.123456+00:00',
            'role': {
                'id': '3',
                'title': 'Member'
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
                'id': '4',
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
                'id': '3',
                'level': 200,
                'title': 'Member'
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
                'id': '5',
                'title': 'Project Owner'
            },
            'usergroup': {
                'id': '4',
                'title': 'Group-11'
            }
        },
        None,
        {
            'addedBy': {
                'profile': {
                    'displayName': 'Danielle Johnson',
                },
                'id': '1'
            },
            'badges': [
            ],
            'clientId': 'member-user-3',
            'id': '6',
            'joinedAt': '2021-01-01T00:00:00.123456+00:00',
            'role': {
                'id': '3',
                'title': 'Member'
            },
            'usergroup': {
                'id': '5',
                'title': 'Group-12'
            }
        },
        {
            'addedBy': {
                'profile': {
                    'displayName': 'Danielle Johnson',
                },
                'id': '1'
            },
            'badges': [
            ],
            'clientId': 'member-user-4',
            'id': '7',
            'joinedAt': '2021-01-01T00:00:00.123456+00:00',
            'role': {
                'id': '3',
                'title': 'Member'
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
                'id': '5',
                'title': 'Project Owner'
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
                'profile': {
                    'displayName': 'Jeffery Wagner',
                },
                'id': '6'
            },
            'badges': [
                'QA'
            ],
            'clientId': '1',
            'id': '1',
            'joinedAt': '2021-01-01T00:00:00.123456+00:00',
            'member': {
                'profile': {
                    'displayName': 'Jeffery Wagner',
                },
                'id': '6'
            },
            'role': {
                'id': '3',
                'level': 200,
                'title': 'Member'
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
        None,
        [
            {
                'arrayErrors': None,
                'clientId': 'member-user-2-with-user-group',
                'field': 'nonFieldErrors',
                'messages': 'This user is added through usergroup: Group-1. Please update the respective usergroup.',
                'objectErrors': None
            }
        ]
    ],
    'result': [
        None,
        None,
        {
            'addedBy': {
                'profile': {
                    'displayName': 'Joshua Walker',
                },
                'id': '2'
            },
            'badges': [
            ],
            'clientId': 'member-user-3',
            'id': '9',
            'joinedAt': '2021-01-01T00:00:00.123456+00:00',
            'member': {
                'profile': {
                    'displayName': 'Debra Gardner',
                },
                'id': '8'
            },
            'role': {
                'id': '3',
                'title': 'Member'
            }
        },
        {
            'addedBy': {
                'profile': {
                    'displayName': 'Joshua Walker',
                },
                'id': '2'
            },
            'badges': [
            ],
            'clientId': 'member-user-4',
            'id': '10',
            'joinedAt': '2021-01-01T00:00:00.123456+00:00',
            'member': {
                'profile': {
                    'displayName': 'Jeffrey Lawrence',
                },
                'id': '9'
            },
            'role': {
                'id': '3',
                'title': 'Member'
            }
        },
        None
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
                'clientId': 'member-user-2-with-user-group',
                'field': 'nonFieldErrors',
                'messages': 'This user is added through usergroup: Group-1. Please update the respective usergroup.',
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
        None,
        {
            'addedBy': {
                'profile': {
                    'displayName': 'Anthony Gonzalez',
                },
                'id': '7'
            },
            'badges': [
            ],
            'clientId': 'member-user-2',
            'id': '2',
            'joinedAt': '2021-01-01T00:00:00.123456+00:00',
            'member': {
                'profile': {
                    'displayName': 'Anthony Gonzalez',
                },
                'id': '7'
            },
            'role': {
                'id': '4',
                'title': 'Admin'
            }
        }
    ]
}

snapshots['TestProjectMembershipMutation::test_user_membership_using_clairvoyan_one_bulk try 1'] = {
    'deletedResult': [
        {
            'addedBy': {
                'profile': {
                    'displayName': 'Jeffery Wagner',
                },
                'id': '6'
            },
            'badges': [
                'QA'
            ],
            'clientId': '1',
            'id': '1',
            'joinedAt': '2021-01-01T00:00:00.123456+00:00',
            'member': {
                'profile': {
                    'displayName': 'Jeffery Wagner',
                },
                'id': '6'
            },
            'role': {
                'id': '3',
                'level': 200,
                'title': 'Member'
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
        None,
        [
            {
                'arrayErrors': None,
                'clientId': 'member-user-2-with-user-group',
                'field': 'nonFieldErrors',
                'messages': 'This user is added through usergroup: Group-1. Please update the respective usergroup.',
                'objectErrors': None
            }
        ]
    ],
    'result': [
        {
            'addedBy': {
                'profile': {
                    'displayName': 'Anthony Gonzalez',
                },
                'id': '7'
            },
            'badges': [
                'QA'
            ],
            'clientId': 'member-user-2',
            'id': '2',
            'joinedAt': '2021-01-01T00:00:00.123456+00:00',
            'member': {
                'profile': {
                    'displayName': 'Anthony Gonzalez',
                },
                'id': '7'
            },
            'role': {
                'id': '5',
                'title': 'Project Owner'
            }
        },
        None,
        {
            'addedBy': {
                'profile': {
                    'displayName': 'Joshua Walker',
                },
                'id': '2'
            },
            'badges': [
            ],
            'clientId': 'member-user-3',
            'id': '9',
            'joinedAt': '2021-01-01T00:00:00.123456+00:00',
            'member': {
                'profile': {
                    'displayName': 'Debra Gardner',
                },
                'id': '8'
            },
            'role': {
                'id': '3',
                'title': 'Member'
            }
        },
        {
            'addedBy': {
                'profile': {
                    'displayName': 'Joshua Walker',
                },
                'id': '2'
            },
            'badges': [
            ],
            'clientId': 'member-user-4',
            'id': '10',
            'joinedAt': '2021-01-01T00:00:00.123456+00:00',
            'member': {
                'profile': {
                    'displayName': 'Jeffrey Lawrence',
                },
                'id': '9'
            },
            'role': {
                'id': '3',
                'title': 'Member'
            }
        },
        None
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
                'clientId': 'member-user-2-with-user-group',
                'field': 'nonFieldErrors',
                'messages': 'This user is added through usergroup: Group-1. Please update the respective usergroup.',
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
                'profile': {
                    'displayName': 'Anthony Gonzalez',
                },
                'id': '7'
            },
            'badges': [
                'QA'
            ],
            'clientId': 'member-user-2',
            'id': '2',
            'joinedAt': '2021-01-01T00:00:00.123456+00:00',
            'member': {
                'profile': {
                    'displayName': 'Anthony Gonzalez',
                },
                'id': '7'
            },
            'role': {
                'id': '5',
                'title': 'Project Owner'
            }
        },
        None,
        None,
        None,
        None,
        None
    ]
}
