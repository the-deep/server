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
                'CAN_USE_IN_OTHER_PROJECTS'
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
                            'version': 1,
                            'widgetId': 'NUMBER'
                        },
                        {
                            'id': '4',
                            'key': 'widget-key-1',
                            'order': 19,
                            'properties': {
                            },
                            'title': 'Widget-1',
                            'version': 1,
                            'widgetId': 'ORGANIGRAM'
                        },
                        {
                            'id': '3',
                            'key': 'widget-key-0',
                            'order': 20,
                            'properties': {
                            },
                            'title': 'Widget-0',
                            'version': 1,
                            'widgetId': 'MULTISELECT'
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
                            'id': '8',
                            'key': 'widget-key-2',
                            'order': 2,
                            'properties': {
                            },
                            'title': 'Widget-2',
                            'version': 1,
                            'widgetId': 'DATE'
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
                            'version': 1,
                            'widgetId': 'SELECT'
                        },
                        {
                            'id': '2',
                            'key': 'widget-key-1',
                            'order': 1,
                            'properties': {
                            },
                            'title': 'Widget-1',
                            'version': 1,
                            'widgetId': 'TIME_RANGE'
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
                    'version': 1,
                    'widgetId': 'SELECT'
                },
                {
                    'id': '12',
                    'key': 'widget-key-2',
                    'order': 18,
                    'properties': {
                    },
                    'title': 'Widget-2',
                    'version': 1,
                    'widgetId': 'MATRIX2D'
                },
                {
                    'id': '11',
                    'key': 'widget-key-1',
                    'order': 19,
                    'properties': {
                    },
                    'title': 'Widget-1',
                    'version': 1,
                    'widgetId': 'TIME'
                }
            ],
            'title': 'AF-0'
        }
    }
}

snapshots['TestAnalysisFrameworkQuery::test_analysis_framework_detail_query without-membership'] = {
    'data': {
        'analysisFramework': {
            'allowedPermissions': [
                'CAN_CLONE_FRAMEWORK',
                'CAN_USE_IN_OTHER_PROJECTS'
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
                            'version': 1,
                            'widgetId': 'NUMBER'
                        },
                        {
                            'id': '4',
                            'key': 'widget-key-1',
                            'order': 19,
                            'properties': {
                            },
                            'title': 'Widget-1',
                            'version': 1,
                            'widgetId': 'ORGANIGRAM'
                        },
                        {
                            'id': '3',
                            'key': 'widget-key-0',
                            'order': 20,
                            'properties': {
                            },
                            'title': 'Widget-0',
                            'version': 1,
                            'widgetId': 'MULTISELECT'
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
                            'id': '8',
                            'key': 'widget-key-2',
                            'order': 2,
                            'properties': {
                            },
                            'title': 'Widget-2',
                            'version': 1,
                            'widgetId': 'DATE'
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
                            'version': 1,
                            'widgetId': 'SELECT'
                        },
                        {
                            'id': '2',
                            'key': 'widget-key-1',
                            'order': 1,
                            'properties': {
                            },
                            'title': 'Widget-1',
                            'version': 1,
                            'widgetId': 'TIME_RANGE'
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
                    'version': 1,
                    'widgetId': 'SELECT'
                },
                {
                    'id': '12',
                    'key': 'widget-key-2',
                    'order': 18,
                    'properties': {
                    },
                    'title': 'Widget-2',
                    'version': 1,
                    'widgetId': 'MATRIX2D'
                },
                {
                    'id': '11',
                    'key': 'widget-key-1',
                    'order': 19,
                    'properties': {
                    },
                    'title': 'Widget-1',
                    'version': 1,
                    'widgetId': 'TIME'
                }
            ],
            'title': 'AF-0'
        }
    }
}

snapshots['TestAnalysisFrameworkQuery::test_analysis_framework_list response-01'] = [
    {
        'clonedFrom': None,
        'description': 'Investment on gun young catch management sense technology check civil quite others his other life edge network wall quite boy those seem shoulder future fall citizen.',
        'id': '2',
        'isPrivate': False,
        'tags': [
            {
                'description': 'Future choice whatever from behavior benefit suggest page southern role movie win her need stop peace technology officer relate animal direction eye.',
                'icon': {
                    'name': 'af-tag-icon/example_AF-Tag-1.png',
                    'url': 'http://testserver/media/af-tag-icon/example_AF-Tag-1.png'
                },
                'id': '2',
                'title': 'AF-Tag-1'
            }
        ],
        'title': 'AF-1'
    },
    {
        'clonedFrom': None,
        'description': 'West then enjoy may condition tree that fear police participant check several.',
        'id': '3',
        'isPrivate': False,
        'tags': [
        ],
        'title': 'AF-2'
    }
]

snapshots['TestAnalysisFrameworkQuery::test_analysis_framework_list response-02'] = [
    {
        'clonedFrom': None,
        'description': 'Investment on gun young catch management sense technology check civil quite others his other life edge network wall quite boy those seem shoulder future fall citizen.',
        'id': '2',
        'isPrivate': False,
        'tags': [
            {
                'description': 'Future choice whatever from behavior benefit suggest page southern role movie win her need stop peace technology officer relate animal direction eye.',
                'icon': {
                    'name': 'af-tag-icon/example_AF-Tag-1.png',
                    'url': 'http://testserver/media/af-tag-icon/example_AF-Tag-1.png'
                },
                'id': '2',
                'title': 'AF-Tag-1'
            }
        ],
        'title': 'AF-1'
    },
    {
        'clonedFrom': None,
        'description': 'West then enjoy may condition tree that fear police participant check several.',
        'id': '3',
        'isPrivate': False,
        'tags': [
        ],
        'title': 'AF-2'
    }
]

snapshots['TestAnalysisFrameworkQuery::test_analysis_framework_list response-03'] = [
    {
        'clonedFrom': None,
        'description': 'Here writer policy news range successful simply director allow firm environment decision wall then fire pretty how trip learn enter east no enjoy.',
        'id': '1',
        'isPrivate': True,
        'tags': [
            {
                'description': 'Each cause bill scientist nation opportunity all behavior discussion own night respond red information last everything thank serve civil.',
                'icon': {
                    'name': 'af-tag-icon/example_AF-Tag-0.png',
                    'url': 'http://testserver/media/af-tag-icon/example_AF-Tag-0.png'
                },
                'id': '1',
                'title': 'AF-Tag-0'
            },
            {
                'description': 'Future choice whatever from behavior benefit suggest page southern role movie win her need stop peace technology officer relate animal direction eye.',
                'icon': {
                    'name': 'af-tag-icon/example_AF-Tag-1.png',
                    'url': 'http://testserver/media/af-tag-icon/example_AF-Tag-1.png'
                },
                'id': '2',
                'title': 'AF-Tag-1'
            }
        ],
        'title': 'AF-0'
    },
    {
        'clonedFrom': None,
        'description': 'Investment on gun young catch management sense technology check civil quite others his other life edge network wall quite boy those seem shoulder future fall citizen.',
        'id': '2',
        'isPrivate': False,
        'tags': [
            {
                'description': 'Future choice whatever from behavior benefit suggest page southern role movie win her need stop peace technology officer relate animal direction eye.',
                'icon': {
                    'name': 'af-tag-icon/example_AF-Tag-1.png',
                    'url': 'http://testserver/media/af-tag-icon/example_AF-Tag-1.png'
                },
                'id': '2',
                'title': 'AF-Tag-1'
            }
        ],
        'title': 'AF-1'
    },
    {
        'clonedFrom': None,
        'description': 'West then enjoy may condition tree that fear police participant check several.',
        'id': '3',
        'isPrivate': False,
        'tags': [
        ],
        'title': 'AF-2'
    }
]
