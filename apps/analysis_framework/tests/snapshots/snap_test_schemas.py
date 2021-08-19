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
                'currentUserRole': 'Owner',
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
                                'widgetId': 'TEXTWIDGET'
                            },
                            {
                                'clientId': 'section-2-text-102-client-id',
                                'id': '4',
                                'key': 'section-2-text-102',
                                'order': 2,
                                'properties': {
                                },
                                'title': 'Section-2-Text-102',
                                'widgetId': 'TEXTWIDGET'
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
                                'widgetId': 'TEXTWIDGET'
                            },
                            {
                                'clientId': 'section-text-102-client-id',
                                'id': '2',
                                'key': 'section-text-102',
                                'order': 2,
                                'properties': {
                                },
                                'title': 'Section-Text-102',
                                'widgetId': 'TEXTWIDGET'
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
                        'widgetId': 'SELECTWIDGET'
                    },
                    {
                        'clientId': 'multi-select-widget-102-client-id',
                        'id': '6',
                        'key': 'multi-select-widget-102-key',
                        'order': 2,
                        'properties': {
                        },
                        'title': 'multi-select-Widget-2',
                        'widgetId': 'MULTISELECTWIDGET'
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
                    'currentUserRole': 'Owner',
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
                                    'id': '7',
                                    'key': 'section-2-text-101',
                                    'order': 1,
                                    'properties': {
                                    },
                                    'title': 'Section-2-Text-101',
                                    'widgetId': 'TEXTWIDGET'
                                },
                                {
                                    'clientId': 'section-2-text-102-client-id',
                                    'id': '4',
                                    'key': 'section-2-text-102',
                                    'order': 2,
                                    'properties': {
                                    },
                                    'title': 'Updated-Section-2-Text-101',
                                    'widgetId': 'TEXTWIDGET'
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
                                    'id': '1',
                                    'key': 'section-text-101',
                                    'order': 1,
                                    'properties': {
                                    },
                                    'title': 'Section-Text-101',
                                    'widgetId': 'TEXTWIDGET'
                                },
                                {
                                    'clientId': 'section-text-102-client-id',
                                    'id': '2',
                                    'key': 'section-text-102',
                                    'order': 2,
                                    'properties': {
                                    },
                                    'title': 'Section-Text-102',
                                    'widgetId': 'TEXTWIDGET'
                                }
                            ]
                        }
                    ],
                    'secondaryTagging': [
                        {
                            'clientId': 'multi-select-widget-102-client-id',
                            'id': '8',
                            'key': 'multi-select-widget-102-key',
                            'order': 2,
                            'properties': {
                            },
                            'title': 'multi-select-Widget-2',
                            'widgetId': 'MULTISELECTWIDGET'
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
                    'messages': 'Only 1 items are allowed. Provided: 2',
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
                                    'messages': 'Only 2 items are allowed. Provided: 4',
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
                                    'messages': 'Only 2 items are allowed. Provided: 4',
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
                    'messages': 'Only 2 items are allowed. Provided: 4',
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

snapshots['TestAnalysisFrameworkQuery::test_analysis_framework_detail_query with-membership'] = {
    'data': {
        'analysisFramework': {
            'currentUserRole': 'Default',
            'description': 'Quality throughout beautiful instead ahead despite measure ago current practice nation determine operation speak.',
            'id': '1',
            'isPrivate': False,
            'members': [
                {
                    'addedBy': None,
                    'id': '1',
                    'joinedAt': '2021-01-01T00:00:00.123456+00:00',
                    'member': {
                        'displayName': 'Joshua Walker',
                        'id': '2'
                    },
                    'role': {
                        'id': '3',
                        'title': 'Default'
                    }
                },
                {
                    'addedBy': None,
                    'id': '2',
                    'joinedAt': '2021-01-01T00:00:00.123456+00:00',
                    'member': {
                        'displayName': 'Danielle Johnson',
                        'id': '1'
                    },
                    'role': {
                        'id': '3',
                        'title': 'Default'
                    }
                }
            ],
            'primaryTagging': [
                {
                    'id': '2',
                    'order': 1,
                    'title': 'Section-1',
                    'tooltip': 'Some tooltip info 102',
                    'widgets': [
                        {
                            'id': '5',
                            'key': 'widget-key-2',
                            'order': 18,
                            'properties': {
                            },
                            'title': 'Widget-2',
                            'widgetId': 'DATEWIDGET'
                        },
                        {
                            'id': '4',
                            'key': 'widget-key-1',
                            'order': 19,
                            'properties': {
                            },
                            'title': 'Widget-1',
                            'widgetId': 'MULTISELECTWIDGET'
                        },
                        {
                            'id': '3',
                            'key': 'widget-key-0',
                            'order': 20,
                            'properties': {
                            },
                            'title': 'Widget-0',
                            'widgetId': 'TEXTWIDGET'
                        }
                    ]
                },
                {
                    'id': '3',
                    'order': 2,
                    'title': 'Section-2',
                    'tooltip': 'Some tooltip info 103',
                    'widgets': [
                        {
                            'id': '6',
                            'key': 'widget-key-0',
                            'order': 0,
                            'properties': {
                            },
                            'title': 'Widget-0',
                            'widgetId': 'SCALEWIDGET'
                        },
                        {
                            'id': '7',
                            'key': 'widget-key-1',
                            'order': 1,
                            'properties': {
                            },
                            'title': 'Widget-1',
                            'widgetId': 'CONDITIONALWIDGET'
                        },
                        {
                            'id': '8',
                            'key': 'widget-key-2',
                            'order': 2,
                            'properties': {
                            },
                            'title': 'Widget-2',
                            'widgetId': 'MATRIX1DWIDGET'
                        },
                        {
                            'id': '9',
                            'key': 'widget-key-3',
                            'order': 3,
                            'properties': {
                            },
                            'title': 'Widget-3',
                            'widgetId': 'MULTISELECTWIDGET'
                        }
                    ]
                },
                {
                    'id': '1',
                    'order': 3,
                    'title': 'Section-0',
                    'tooltip': 'Some tooltip info 101',
                    'widgets': [
                        {
                            'id': '1',
                            'key': 'widget-key-0',
                            'order': 0,
                            'properties': {
                            },
                            'title': 'Widget-0',
                            'widgetId': 'CONDITIONALWIDGET'
                        },
                        {
                            'id': '2',
                            'key': 'widget-key-1',
                            'order': 1,
                            'properties': {
                            },
                            'title': 'Widget-1',
                            'widgetId': 'SELECTWIDGET'
                        }
                    ]
                }
            ],
            'secondaryTagging': [
                {
                    'id': '13',
                    'key': 'widget-key-3',
                    'order': 17,
                    'properties': {
                    },
                    'title': 'Widget-3',
                    'widgetId': 'TIMERANGEWIDGET'
                },
                {
                    'id': '12',
                    'key': 'widget-key-2',
                    'order': 18,
                    'properties': {
                    },
                    'title': 'Widget-2',
                    'widgetId': 'MATRIX1DWIDGET'
                },
                {
                    'id': '11',
                    'key': 'widget-key-1',
                    'order': 19,
                    'properties': {
                    },
                    'title': 'Widget-1',
                    'widgetId': 'GEOWIDGET'
                },
                {
                    'id': '10',
                    'key': 'widget-key-0',
                    'order': 20,
                    'properties': {
                    },
                    'title': 'Widget-0',
                    'widgetId': 'NUMBERWIDGET'
                }
            ],
            'title': 'AF-3'
        }
    }
}

snapshots['TestAnalysisFrameworkQuery::test_analysis_framework_detail_query without-membership'] = {
    'data': {
        'analysisFramework': {
            'currentUserRole': None,
            'description': 'Quality throughout beautiful instead ahead despite measure ago current practice nation determine operation speak.',
            'id': '1',
            'isPrivate': False,
            'members': [
            ],
            'primaryTagging': [
                {
                    'id': '2',
                    'order': 1,
                    'title': 'Section-1',
                    'tooltip': 'Some tooltip info 102',
                    'widgets': [
                        {
                            'id': '5',
                            'key': 'widget-key-2',
                            'order': 18,
                            'properties': {
                            },
                            'title': 'Widget-2',
                            'widgetId': 'DATEWIDGET'
                        },
                        {
                            'id': '4',
                            'key': 'widget-key-1',
                            'order': 19,
                            'properties': {
                            },
                            'title': 'Widget-1',
                            'widgetId': 'MULTISELECTWIDGET'
                        },
                        {
                            'id': '3',
                            'key': 'widget-key-0',
                            'order': 20,
                            'properties': {
                            },
                            'title': 'Widget-0',
                            'widgetId': 'TEXTWIDGET'
                        }
                    ]
                },
                {
                    'id': '3',
                    'order': 2,
                    'title': 'Section-2',
                    'tooltip': 'Some tooltip info 103',
                    'widgets': [
                        {
                            'id': '6',
                            'key': 'widget-key-0',
                            'order': 0,
                            'properties': {
                            },
                            'title': 'Widget-0',
                            'widgetId': 'SCALEWIDGET'
                        },
                        {
                            'id': '7',
                            'key': 'widget-key-1',
                            'order': 1,
                            'properties': {
                            },
                            'title': 'Widget-1',
                            'widgetId': 'CONDITIONALWIDGET'
                        },
                        {
                            'id': '8',
                            'key': 'widget-key-2',
                            'order': 2,
                            'properties': {
                            },
                            'title': 'Widget-2',
                            'widgetId': 'MATRIX1DWIDGET'
                        },
                        {
                            'id': '9',
                            'key': 'widget-key-3',
                            'order': 3,
                            'properties': {
                            },
                            'title': 'Widget-3',
                            'widgetId': 'MULTISELECTWIDGET'
                        }
                    ]
                },
                {
                    'id': '1',
                    'order': 3,
                    'title': 'Section-0',
                    'tooltip': 'Some tooltip info 101',
                    'widgets': [
                        {
                            'id': '1',
                            'key': 'widget-key-0',
                            'order': 0,
                            'properties': {
                            },
                            'title': 'Widget-0',
                            'widgetId': 'CONDITIONALWIDGET'
                        },
                        {
                            'id': '2',
                            'key': 'widget-key-1',
                            'order': 1,
                            'properties': {
                            },
                            'title': 'Widget-1',
                            'widgetId': 'SELECTWIDGET'
                        }
                    ]
                }
            ],
            'secondaryTagging': [
                {
                    'id': '13',
                    'key': 'widget-key-3',
                    'order': 17,
                    'properties': {
                    },
                    'title': 'Widget-3',
                    'widgetId': 'TIMERANGEWIDGET'
                },
                {
                    'id': '12',
                    'key': 'widget-key-2',
                    'order': 18,
                    'properties': {
                    },
                    'title': 'Widget-2',
                    'widgetId': 'MATRIX1DWIDGET'
                },
                {
                    'id': '11',
                    'key': 'widget-key-1',
                    'order': 19,
                    'properties': {
                    },
                    'title': 'Widget-1',
                    'widgetId': 'GEOWIDGET'
                },
                {
                    'id': '10',
                    'key': 'widget-key-0',
                    'order': 20,
                    'properties': {
                    },
                    'title': 'Widget-0',
                    'widgetId': 'NUMBERWIDGET'
                }
            ],
            'title': 'AF-3'
        }
    }
}
