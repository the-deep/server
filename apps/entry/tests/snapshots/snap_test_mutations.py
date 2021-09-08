# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot


snapshots = Snapshot()

snapshots['TestEntryMutation::test_entry_bulk error'] = {
    'data': {
        'project': {
            'entryBulk': {
                'deletedResult': [
                    {
                        'attributes': None,
                        'clientId': '1',
                        'droppedExcerpt': '',
                        'entryType': 'DATA_SERIES',
                        'excerpt': 'FfWdhjOkYRBMeyyMDHqJaRUhRIWrXPvhsBkDaUUqGWlGgOtOGMmjxWkIXHaMuFbhxZtpdpKffUFeWIXiiQEJkqHMBnIWUSmTtzQP',
                        'highlightHidden': False,
                        'id': '1',
                        'image': {
                            'id': '4',
                            'title': 'file-3'
                        },
                        'informationDate': None,
                        'order': 1
                    }
                ],
                'errors': [
                    [
                        {
                            'arrayErrors': None,
                            'clientId': 'entry-old-101 (UPDATED)',
                            'field': 'image',
                            'messages': "You don't have permission to attach image: file-1",
                            'objectErrors': None
                        }
                    ],
                    [
                        {
                            'arrayErrors': None,
                            'clientId': 'entry-new-102',
                            'field': 'image',
                            'messages': "You don't have permission to attach image: file-1",
                            'objectErrors': None
                        }
                    ]
                ],
                'result': [
                    None,
                    None
                ]
            }
        }
    }
}

snapshots['TestEntryMutation::test_entry_bulk success'] = {
    'data': {
        'project': {
            'entryBulk': {
                'deletedResult': [
                ],
                'errors': [
                    None,
                    None
                ],
                'result': [
                    {
                        'attributes': [
                            {
                                'clientId': 'client-id-old-new-attribute-1',
                                'data': {
                                },
                                'id': '2',
                                'widget': '1',
                                'widgetType': 'MATRIX2D'
                            },
                            {
                                'clientId': 'client-id-old-attribute-1',
                                'data': {
                                },
                                'id': '1',
                                'widget': '1',
                                'widgetType': 'MATRIX2D'
                            }
                        ],
                        'clientId': 'entry-old-101 (UPDATED)',
                        'droppedExcerpt': 'This is a dropped text (UPDATED)',
                        'entryType': 'EXCERPT',
                        'excerpt': 'This is a text (UPDATED)',
                        'highlightHidden': False,
                        'id': '2',
                        'image': {
                            'id': '3',
                            'title': 'file-2'
                        },
                        'informationDate': '2021-01-01',
                        'order': 1
                    },
                    {
                        'attributes': [
                            {
                                'clientId': 'client-id-new-attribute-1',
                                'data': {
                                },
                                'id': '3',
                                'widget': '1',
                                'widgetType': 'MATRIX2D'
                            }
                        ],
                        'clientId': 'entry-new-102',
                        'droppedExcerpt': 'This is a dropped text (NEW)',
                        'entryType': 'EXCERPT',
                        'excerpt': 'This is a text (NEW)',
                        'highlightHidden': False,
                        'id': '3',
                        'image': {
                            'id': '3',
                            'title': 'file-2'
                        },
                        'informationDate': '2021-01-01',
                        'order': 1
                    }
                ]
            }
        }
    }
}

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
                            'widgetType': 'MATRIX2D'
                        },
                        {
                            'clientId': 'client-id-attribute-2',
                            'data': {
                            },
                            'id': '2',
                            'widget': '2',
                            'widgetType': 'SELECT'
                        },
                        {
                            'clientId': 'client-id-attribute-3',
                            'data': {
                            },
                            'id': '3',
                            'widget': '3',
                            'widgetType': 'NUMBER'
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

snapshots['TestEntryMutation::test_entry_update error'] = {
    'data': {
        'project': {
            'entryUpdate': {
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

snapshots['TestEntryMutation::test_entry_update success'] = {
    'data': {
        'project': {
            'entryUpdate': {
                'errors': None,
                'ok': True,
                'result': {
                    'attributes': [
                        {
                            'clientId': 'client-id-attribute-3',
                            'data': {
                            },
                            'id': '3',
                            'widget': '1',
                            'widgetType': 'MATRIX2D'
                        },
                        {
                            'clientId': 'client-id-attribute-1',
                            'data': {
                            },
                            'id': '1',
                            'widget': '1',
                            'widgetType': 'MATRIX2D'
                        },
                        {
                            'clientId': 'client-id-attribute-2',
                            'data': {
                            },
                            'id': '2',
                            'widget': '2',
                            'widgetType': 'SELECT'
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
