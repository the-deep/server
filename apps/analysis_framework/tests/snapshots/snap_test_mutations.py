# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot


snapshots = Snapshot()

snapshots['TestAnalysisFrameworkMutationSnapShotTestCase::test_analysis_framework_create errors'] = {
    'data': {
        '__typename': 'Mutation',
        'analysisFrameworkCreate': {
            'errors': [
                {
                    'arrayErrors': None,
                    'clientId': None,
                    'field': 'title',
                    'messages': 'This field may not be blank.',
                    'objectErrors': None
                },
                {
                    'arrayErrors': [
                        {
                            'clientId': 'section-101',
                            'messages': None,
                            'objectErrors': [
                                {
                                    'arrayErrors': None,
                                    'clientId': 'section-101',
                                    'field': 'title',
                                    'messages': 'This field may not be blank.',
                                    'objectErrors': None
                                },
                                {
                                    'arrayErrors': [
                                        {
                                            'clientId': 'section-text-101-client-id',
                                            'messages': None,
                                            'objectErrors': [
                                                {
                                                    'arrayErrors': None,
                                                    'clientId': 'section-text-101-client-id',
                                                    'field': 'title',
                                                    'messages': 'This field may not be blank.',
                                                    'objectErrors': None
                                                }
                                            ]
                                        },
                                        {
                                            'clientId': 'section-text-102-client-id',
                                            'messages': None,
                                            'objectErrors': [
                                                {
                                                    'arrayErrors': None,
                                                    'clientId': 'section-text-102-client-id',
                                                    'field': 'title',
                                                    'messages': 'This field may not be blank.',
                                                    'objectErrors': None
                                                }
                                            ]
                                        }
                                    ],
                                    'clientId': 'section-101',
                                    'field': 'widgets',
                                    'messages': None,
                                    'objectErrors': None
                                }
                            ]
                        },
                        {
                            'clientId': 'section-102',
                            'messages': None,
                            'objectErrors': [
                                {
                                    'arrayErrors': None,
                                    'clientId': 'section-102',
                                    'field': 'title',
                                    'messages': 'This field may not be blank.',
                                    'objectErrors': None
                                }
                            ]
                        }
                    ],
                    'clientId': None,
                    'field': 'primaryTagging',
                    'messages': None,
                    'objectErrors': None
                },
                {
                    'arrayErrors': [
                        {
                            'clientId': 'select-widget-101-client-id',
                            'messages': None,
                            'objectErrors': [
                                {
                                    'arrayErrors': None,
                                    'clientId': 'select-widget-101-client-id',
                                    'field': 'title',
                                    'messages': 'This field may not be blank.',
                                    'objectErrors': None
                                }
                            ]
                        }
                    ],
                    'clientId': None,
                    'field': 'secondaryTagging',
                    'messages': None,
                    'objectErrors': None
                }
            ],
            'ok': False,
            'result': None
        }
    }
}

snapshots['TestAnalysisFrameworkMutationSnapShotTestCase::test_analysis_framework_create success'] = {
    'data': {
        '__typename': 'Mutation',
        'analysisFrameworkCreate': {
            'errors': None,
            'ok': True,
            'result': {
                'currentUserRole': 'OWNER',
                'description': 'Af description',
                'id': '1',
                'isPrivate': False,
                'primaryTagging': [
                    {
                        'clientId': 'section-102',
                        'id': '2',
                        'order': 1,
                        'title': 'Section 102',
                        'tooltip': 'Tooltip for section 102',
                        'widgets': [
                            {
                                'clientId': 'section-2-text-101-client-id',
                                'id': '3',
                                'key': 'section-2-text-101',
                                'order': 1,
                                'properties': {
                                },
                                'title': 'Section-2-Text-101',
                                'version': 1,
                                'widgetId': 'TEXT'
                            },
                            {
                                'clientId': 'section-2-text-102-client-id',
                                'id': '4',
                                'key': 'section-2-text-102',
                                'order': 2,
                                'properties': {
                                },
                                'title': 'Section-2-Text-102',
                                'version': 1,
                                'widgetId': 'TEXT'
                            }
                        ]
                    },
                    {
                        'clientId': 'section-101',
                        'id': '1',
                        'order': 2,
                        'title': 'Section 101',
                        'tooltip': 'Tooltip for section 101',
                        'widgets': [
                            {
                                'clientId': 'section-text-101-client-id',
                                'id': '1',
                                'key': 'section-text-101',
                                'order': 1,
                                'properties': {
                                },
                                'title': 'Section-Text-101',
                                'version': 1,
                                'widgetId': 'TEXT'
                            },
                            {
                                'clientId': 'section-text-102-client-id',
                                'id': '2',
                                'key': 'section-text-102',
                                'order': 2,
                                'properties': {
                                },
                                'title': 'Section-Text-102',
                                'version': 1,
                                'widgetId': 'TEXT'
                            }
                        ]
                    }
                ],
                'secondaryTagging': [
                    {
                        'clientId': 'select-widget-101-client-id',
                        'id': '5',
                        'key': 'select-widget-101-key',
                        'order': 1,
                        'properties': {
                        },
                        'title': 'Select-Widget-1',
                        'version': 1,
                        'widgetId': 'SELECT'
                    },
                    {
                        'clientId': 'multi-select-widget-102-client-id',
                        'id': '6',
                        'key': 'multi-select-widget-102-key',
                        'order': 2,
                        'properties': {
                        },
                        'title': 'multi-select-Widget-2',
                        'version': 1,
                        'widgetId': 'MULTISELECT'
                    }
                ],
                'title': 'AF (TEST)'
            }
        }
    }
}

snapshots['TestAnalysisFrameworkMutationSnapShotTestCase::test_analysis_framework_membership_bulk try 1'] = {
    'deletedResult': [
        {
            'addedBy': None,
            'clientId': '1',
            'id': '1',
            'joinedAt': '2021-01-01T00:00:00.123456+00:00',
            'member': {
                'displayName': 'Clayton Hall',
                'id': '5'
            },
            'role': {
                'id': '3',
                'title': 'Default'
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
            'addedBy': None,
            'clientId': 'member-user-2',
            'id': '2',
            'joinedAt': '2021-01-01T00:00:00.123456+00:00',
            'member': {
                'displayName': 'Carolyn Hoffman',
                'id': '6'
            },
            'role': {
                'id': '2',
                'title': 'Owner'
            }
        },
        None,
        {
            'addedBy': {
                'displayName': 'Donald Garcia',
                'id': '2'
            },
            'clientId': 'member-user-3',
            'id': '7',
            'joinedAt': '2021-01-01T00:00:00.123456+00:00',
            'member': {
                'displayName': 'Jennifer Miles',
                'id': '7'
            },
            'role': {
                'id': '3',
                'title': 'Default'
            }
        },
        {
            'addedBy': {
                'displayName': 'Donald Garcia',
                'id': '2'
            },
            'clientId': 'member-user-4',
            'id': '8',
            'joinedAt': '2021-01-01T00:00:00.123456+00:00',
            'member': {
                'displayName': 'Robert Cole',
                'id': '8'
            },
            'role': {
                'id': '1',
                'title': 'Editor'
            }
        }
    ]
}

snapshots['TestAnalysisFrameworkMutationSnapShotTestCase::test_analysis_framework_membership_bulk try 2'] = {
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
            'addedBy': None,
            'clientId': 'member-user-2',
            'id': '2',
            'joinedAt': '2021-01-01T00:00:00.123456+00:00',
            'member': {
                'displayName': 'Carolyn Hoffman',
                'id': '6'
            },
            'role': {
                'id': '2',
                'title': 'Owner'
            }
        },
        None,
        None
    ]
}

snapshots['TestAnalysisFrameworkMutationSnapShotTestCase::test_analysis_framework_update created'] = {
    'currentUserRole': 'OWNER',
    'description': 'Af description',
    'id': '1',
    'isPrivate': False,
    'primaryTagging': [
        {
            'clientId': 'section-102',
            'id': '2',
            'order': 1,
            'title': 'Section 102',
            'tooltip': 'Tooltip for section 102',
            'widgets': [
                {
                    'clientId': 'section-2-text-101-client-id',
                    'id': '3',
                    'key': 'section-2-text-101',
                    'order': 1,
                    'properties': {
                    },
                    'title': 'Section-2-Text-101',
                    'version': 1,
                    'widgetId': 'TEXT'
                },
                {
                    'clientId': 'section-2-text-102-client-id',
                    'id': '4',
                    'key': 'section-2-text-102',
                    'order': 2,
                    'properties': {
                    },
                    'title': 'Section-2-Text-102',
                    'version': 1,
                    'widgetId': 'TEXT'
                }
            ]
        },
        {
            'clientId': 'section-101',
            'id': '1',
            'order': 2,
            'title': 'Section 101',
            'tooltip': 'Tooltip for section 101',
            'widgets': [
                {
                    'clientId': 'section-text-101-client-id',
                    'id': '1',
                    'key': 'section-text-101',
                    'order': 1,
                    'properties': {
                    },
                    'title': 'Section-Text-101',
                    'version': 1,
                    'widgetId': 'TEXT'
                },
                {
                    'clientId': 'section-text-102-client-id',
                    'id': '2',
                    'key': 'section-text-102',
                    'order': 2,
                    'properties': {
                    },
                    'title': 'Section-Text-102',
                    'version': 1,
                    'widgetId': 'TEXT'
                }
            ]
        }
    ],
    'secondaryTagging': [
        {
            'clientId': 'select-widget-101-client-id',
            'id': '5',
            'key': 'select-widget-101-key',
            'order': 1,
            'properties': {
            },
            'title': 'Select-Widget-1',
            'version': 1,
            'widgetId': 'SELECT'
        },
        {
            'clientId': 'multi-select-widget-102-client-id',
            'id': '6',
            'key': 'multi-select-widget-102-key',
            'order': 2,
            'properties': {
            },
            'title': 'multi-select-Widget-2',
            'version': 1,
            'widgetId': 'MULTISELECT'
        }
    ],
    'title': 'AF (TEST)'
}

snapshots['TestAnalysisFrameworkMutationSnapShotTestCase::test_analysis_framework_update errors'] = {
    'data': {
        '__typename': 'Mutation',
        'analysisFramework': {
            'analysisFrameworkUpdate': {
                'errors': [
                    {
                        'arrayErrors': None,
                        'clientId': None,
                        'field': 'title',
                        'messages': 'This field may not be blank.',
                        'objectErrors': None
                    },
                    {
                        'arrayErrors': [
                            {
                                'clientId': 'section-102',
                                'messages': None,
                                'objectErrors': [
                                    {
                                        'arrayErrors': None,
                                        'clientId': 'section-102',
                                        'field': 'title',
                                        'messages': 'This field may not be blank.',
                                        'objectErrors': None
                                    }
                                ]
                            }
                        ],
                        'clientId': None,
                        'field': 'primaryTagging',
                        'messages': None,
                        'objectErrors': None
                    }
                ],
                'ok': False,
                'result': None
            }
        }
    }
}

snapshots['TestAnalysisFrameworkMutationSnapShotTestCase::test_analysis_framework_update success'] = {
    'data': {
        '__typename': 'Mutation',
        'analysisFramework': {
            'analysisFrameworkUpdate': {
                'errors': None,
                'ok': True,
                'result': {
                    'currentUserRole': 'OWNER',
                    'description': 'Updated Af description',
                    'id': '1',
                    'isPrivate': False,
                    'primaryTagging': [
                        {
                            'clientId': 'section-102',
                            'id': '2',
                            'order': 1,
                            'title': 'Updated Section 102',
                            'tooltip': 'Tooltip for section 102',
                            'widgets': [
                                {
                                    'clientId': 'section-2-text-101-client-id',
                                    'conditional': None,
                                    'id': '7',
                                    'key': 'section-2-text-101',
                                    'order': 1,
                                    'properties': {
                                    },
                                    'title': 'Section-2-Text-101',
                                    'version': 1,
                                    'widgetId': 'TEXT'
                                },
                                {
                                    'clientId': 'section-2-text-102-client-id',
                                    'conditional': None,
                                    'id': '4',
                                    'key': 'section-2-text-102',
                                    'order': 2,
                                    'properties': {
                                    },
                                    'title': 'Updated-Section-2-Text-101',
                                    'version': 1,
                                    'widgetId': 'TEXT'
                                }
                            ]
                        },
                        {
                            'clientId': 'section-101',
                            'id': '3',
                            'order': 2,
                            'title': 'Section 101',
                            'tooltip': 'Tooltip for section 101',
                            'widgets': [
                                {
                                    'clientId': 'section-text-101-client-id',
                                    'conditional': None,
                                    'id': '1',
                                    'key': 'section-text-101',
                                    'order': 1,
                                    'properties': {
                                    },
                                    'title': 'Section-Text-101',
                                    'version': 1,
                                    'widgetId': 'TEXT'
                                },
                                {
                                    'clientId': 'section-text-102-client-id',
                                    'conditional': None,
                                    'id': '2',
                                    'key': 'section-text-102',
                                    'order': 2,
                                    'properties': {
                                    },
                                    'title': 'Section-Text-102',
                                    'version': 1,
                                    'widgetId': 'TEXT'
                                }
                            ]
                        }
                    ],
                    'secondaryTagging': [
                        {
                            'clientId': 'multi-select-widget-102-client-id',
                            'conditional': None,
                            'id': '8',
                            'key': 'multi-select-widget-102-key',
                            'order': 2,
                            'properties': {
                            },
                            'title': 'multi-select-Widget-2',
                            'version': 1,
                            'widgetId': 'MULTISELECT'
                        }
                    ],
                    'title': 'Updated AF (TEST)'
                }
            }
        }
    }
}

snapshots['TestAnalysisFrameworkMutationSnapShotTestCase::test_analysis_framework_update with-conditionals-add'] = {
    'data': {
        '__typename': 'Mutation',
        'analysisFramework': {
            'analysisFrameworkUpdate': {
                'errors': None,
                'ok': True,
                'result': {
                    'currentUserRole': 'OWNER',
                    'description': 'Updated Af description',
                    'id': '1',
                    'isPrivate': False,
                    'primaryTagging': [
                        {
                            'clientId': 'section-102',
                            'id': '2',
                            'order': 1,
                            'title': 'Updated Section 102',
                            'tooltip': 'Tooltip for section 102',
                            'widgets': [
                                {
                                    'clientId': 'section-2-text-101-client-id',
                                    'conditional': None,
                                    'id': '10',
                                    'key': 'section-2-text-101',
                                    'order': 1,
                                    'properties': {
                                    },
                                    'title': 'Section-2-Text-101',
                                    'version': 1,
                                    'widgetId': 'TEXT'
                                },
                                {
                                    'clientId': 'section-2-text-102-client-id',
                                    'conditional': {
                                        'conditions': [
                                        ],
                                        'parentWidget': '1',
                                        'parentWidgetType': 'TEXT'
                                    },
                                    'id': '4',
                                    'key': 'section-2-text-102',
                                    'order': 2,
                                    'properties': {
                                    },
                                    'title': 'Updated-Section-2-Text-101',
                                    'version': 1,
                                    'widgetId': 'TEXT'
                                }
                            ]
                        },
                        {
                            'clientId': 'section-101',
                            'id': '4',
                            'order': 2,
                            'title': 'Section 101',
                            'tooltip': 'Tooltip for section 101',
                            'widgets': [
                                {
                                    'clientId': 'section-text-101-client-id',
                                    'conditional': None,
                                    'id': '1',
                                    'key': 'section-text-101',
                                    'order': 1,
                                    'properties': {
                                    },
                                    'title': 'Section-Text-101',
                                    'version': 1,
                                    'widgetId': 'TEXT'
                                },
                                {
                                    'clientId': 'section-text-102-client-id',
                                    'conditional': None,
                                    'id': '2',
                                    'key': 'section-text-102',
                                    'order': 2,
                                    'properties': {
                                    },
                                    'title': 'Section-Text-102',
                                    'version': 1,
                                    'widgetId': 'TEXT'
                                }
                            ]
                        }
                    ],
                    'secondaryTagging': [
                        {
                            'clientId': 'multi-select-widget-102-client-id',
                            'conditional': {
                                'conditions': [
                                ],
                                'parentWidget': '1',
                                'parentWidgetType': 'TEXT'
                            },
                            'id': '11',
                            'key': 'multi-select-widget-102-key',
                            'order': 2,
                            'properties': {
                            },
                            'title': 'multi-select-Widget-2',
                            'version': 1,
                            'widgetId': 'MULTISELECT'
                        }
                    ],
                    'title': 'Updated AF (TEST)'
                }
            }
        }
    }
}

snapshots['TestAnalysisFrameworkMutationSnapShotTestCase::test_analysis_framework_update with-conditionals-remove'] = {
    'data': {
        '__typename': 'Mutation',
        'analysisFramework': {
            'analysisFrameworkUpdate': {
                'errors': None,
                'ok': True,
                'result': {
                    'currentUserRole': 'OWNER',
                    'description': 'Updated Af description',
                    'id': '1',
                    'isPrivate': False,
                    'primaryTagging': [
                        {
                            'clientId': 'section-102',
                            'id': '2',
                            'order': 1,
                            'title': 'Updated Section 102',
                            'tooltip': 'Tooltip for section 102',
                            'widgets': [
                                {
                                    'clientId': 'section-2-text-101-client-id',
                                    'conditional': None,
                                    'id': '12',
                                    'key': 'section-2-text-101',
                                    'order': 1,
                                    'properties': {
                                    },
                                    'title': 'Section-2-Text-101',
                                    'version': 1,
                                    'widgetId': 'TEXT'
                                },
                                {
                                    'clientId': 'section-2-text-102-client-id',
                                    'conditional': {
                                        'conditions': [
                                        ],
                                        'parentWidget': '1',
                                        'parentWidgetType': 'TEXT'
                                    },
                                    'id': '4',
                                    'key': 'section-2-text-102',
                                    'order': 2,
                                    'properties': {
                                    },
                                    'title': 'Updated-Section-2-Text-101',
                                    'version': 1,
                                    'widgetId': 'TEXT'
                                }
                            ]
                        },
                        {
                            'clientId': 'section-101',
                            'id': '5',
                            'order': 2,
                            'title': 'Section 101',
                            'tooltip': 'Tooltip for section 101',
                            'widgets': [
                                {
                                    'clientId': 'section-text-101-client-id',
                                    'conditional': None,
                                    'id': '1',
                                    'key': 'section-text-101',
                                    'order': 1,
                                    'properties': {
                                    },
                                    'title': 'Section-Text-101',
                                    'version': 1,
                                    'widgetId': 'TEXT'
                                },
                                {
                                    'clientId': 'section-text-102-client-id',
                                    'conditional': None,
                                    'id': '2',
                                    'key': 'section-text-102',
                                    'order': 2,
                                    'properties': {
                                    },
                                    'title': 'Section-Text-102',
                                    'version': 1,
                                    'widgetId': 'TEXT'
                                }
                            ]
                        }
                    ],
                    'secondaryTagging': [
                        {
                            'clientId': 'multi-select-widget-102-client-id',
                            'conditional': None,
                            'id': '13',
                            'key': 'multi-select-widget-102-key',
                            'order': 2,
                            'properties': {
                            },
                            'title': 'multi-select-Widget-2',
                            'version': 1,
                            'widgetId': 'MULTISELECT'
                        }
                    ],
                    'title': 'Updated AF (TEST)'
                }
            }
        }
    }
}

snapshots['TestAnalysisFrameworkMutationSnapShotTestCase::test_widgets_limit failure-section-level'] = {
    'errors': [
        {
            'arrayErrors': [
                {
                    'clientId': 'nonMemberErrors',
                    'messages': 'Only 1 sections are allowed. Provided: 2',
                    'objectErrors': None
                }
            ],
            'clientId': None,
            'field': 'primaryTagging',
            'messages': None,
            'objectErrors': None
        }
    ],
    'ok': False,
    'result': None
}

snapshots['TestAnalysisFrameworkMutationSnapShotTestCase::test_widgets_limit failure-widget-level'] = {
    'errors': [
        {
            'arrayErrors': [
                {
                    'clientId': 'section-0',
                    'messages': None,
                    'objectErrors': [
                        {
                            'arrayErrors': [
                                {
                                    'clientId': 'nonMemberErrors',
                                    'messages': 'Only 2 widgets are allowed. Provided: 4',
                                    'objectErrors': None
                                }
                            ],
                            'clientId': 'section-0',
                            'field': 'widgets',
                            'messages': None,
                            'objectErrors': None
                        }
                    ]
                },
                {
                    'clientId': 'section-1',
                    'messages': None,
                    'objectErrors': [
                        {
                            'arrayErrors': [
                                {
                                    'clientId': 'nonMemberErrors',
                                    'messages': 'Only 2 widgets are allowed. Provided: 4',
                                    'objectErrors': None
                                }
                            ],
                            'clientId': 'section-1',
                            'field': 'widgets',
                            'messages': None,
                            'objectErrors': None
                        }
                    ]
                }
            ],
            'clientId': None,
            'field': 'primaryTagging',
            'messages': None,
            'objectErrors': None
        },
        {
            'arrayErrors': [
                {
                    'clientId': 'nonMemberErrors',
                    'messages': 'Only 2 widgets are allowed. Provided: 4',
                    'objectErrors': None
                }
            ],
            'clientId': None,
            'field': 'secondaryTagging',
            'messages': None,
            'objectErrors': None
        }
    ],
    'ok': False,
    'result': None
}
