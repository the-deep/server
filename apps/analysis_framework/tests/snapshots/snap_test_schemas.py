# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot


snapshots = Snapshot()

snapshots['TestAnalysisFrameworkQuery::test_analysis_framework_detail_query with-membership'] = {
    'data': {
        'analysisFramework': {
            'allowedPermissions': [
                'CAN_CLONE_FRAMEWORK',
                'CAN_USE_IN_OTHER_PROJECTS',
            ],
            'currentUserRole': 'DEFAULT',
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
                            'widgetId': 'DATE',
                            'version': 1,
                        },
                        {
                            'id': '4',
                            'key': 'widget-key-1',
                            'order': 19,
                            'properties': {
                            },
                            'title': 'Widget-1',
                            'widgetId': 'MULTISELECT',
                            'version': 1,
                        },
                        {
                            'id': '3',
                            'key': 'widget-key-0',
                            'order': 20,
                            'properties': {
                            },
                            'title': 'Widget-0',
                            'widgetId': 'TEXT',
                            'version': 1,
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
                            'widgetId': 'SCALE',
                            'version': 1,
                        },
                        {
                            'id': '8',
                            'key': 'widget-key-2',
                            'order': 2,
                            'properties': {
                            },
                            'title': 'Widget-2',
                            'widgetId': 'MATRIX1D',
                            'version': 1,
                        },
                        {
                            'id': '9',
                            'key': 'widget-key-3',
                            'order': 3,
                            'properties': {
                            },
                            'title': 'Widget-3',
                            'widgetId': 'MULTISELECT',
                            'version': 1,
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
                            'id': '2',
                            'key': 'widget-key-1',
                            'order': 1,
                            'properties': {
                            },
                            'title': 'Widget-1',
                            'widgetId': 'SELECT',
                            'version': 1,
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
                    'widgetId': 'TIME_RANGE',
                    'version': 1,
                },
                {
                    'id': '12',
                    'key': 'widget-key-2',
                    'order': 18,
                    'properties': {
                    },
                    'title': 'Widget-2',
                    'widgetId': 'MATRIX1D',
                    'version': 1,
                },
                {
                    'id': '11',
                    'key': 'widget-key-1',
                    'order': 19,
                    'properties': {
                    },
                    'title': 'Widget-1',
                    'widgetId': 'GEO',
                    'version': 1,
                },
                {
                    'id': '10',
                    'key': 'widget-key-0',
                    'order': 20,
                    'properties': {
                    },
                    'title': 'Widget-0',
                    'widgetId': 'NUMBER',
                    'version': 1,
                }
            ],
            'title': 'AF-0',
        }
    }
}

snapshots['TestAnalysisFrameworkQuery::test_analysis_framework_detail_query without-membership'] = {
    'data': {
        'analysisFramework': {
            'allowedPermissions': [
                'CAN_CLONE_FRAMEWORK',
                'CAN_USE_IN_OTHER_PROJECTS',
            ],
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
                            'widgetId': 'DATE',
                            'version': 1,
                        },
                        {
                            'id': '4',
                            'key': 'widget-key-1',
                            'order': 19,
                            'properties': {
                            },
                            'title': 'Widget-1',
                            'widgetId': 'MULTISELECT',
                            'version': 1,
                        },
                        {
                            'id': '3',
                            'key': 'widget-key-0',
                            'order': 20,
                            'properties': {
                            },
                            'title': 'Widget-0',
                            'widgetId': 'TEXT',
                            'version': 1,
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
                            'widgetId': 'SCALE',
                            'version': 1,
                        },
                        {
                            'id': '8',
                            'key': 'widget-key-2',
                            'order': 2,
                            'properties': {
                            },
                            'title': 'Widget-2',
                            'widgetId': 'MATRIX1D',
                            'version': 1,
                        },
                        {
                            'id': '9',
                            'key': 'widget-key-3',
                            'order': 3,
                            'properties': {
                            },
                            'title': 'Widget-3',
                            'widgetId': 'MULTISELECT',
                            'version': 1,
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
                            'id': '2',
                            'key': 'widget-key-1',
                            'order': 1,
                            'properties': {
                            },
                            'title': 'Widget-1',
                            'widgetId': 'SELECT',
                            'version': 1,
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
                    'widgetId': 'TIME_RANGE',
                    'version': 1,
                },
                {
                    'id': '12',
                    'key': 'widget-key-2',
                    'order': 18,
                    'properties': {
                    },
                    'title': 'Widget-2',
                    'widgetId': 'MATRIX1D',
                    'version': 1,
                },
                {
                    'id': '11',
                    'key': 'widget-key-1',
                    'order': 19,
                    'properties': {
                    },
                    'title': 'Widget-1',
                    'widgetId': 'GEO',
                    'version': 1,
                },
                {
                    'id': '10',
                    'key': 'widget-key-0',
                    'order': 20,
                    'properties': {
                    },
                    'title': 'Widget-0',
                    'widgetId': 'NUMBER',
                    'version': 1,
                }
            ],
            'title': 'AF-0',
        }
    }
}
