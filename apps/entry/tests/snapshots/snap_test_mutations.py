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
                        'excerpt': 'fWdhjOkYRBMeyyMDHqJaRUhRIWrXPvhsBkDaUUqGWlGgOtOGMmjxWkIXHaMuFbhxZtpdpKffUFeWIXiiQEJkqHMBnIWUSmTtzQPx',
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
                                'widgetType': 'TIME_RANGE'
                            },
                            {
                                'clientId': 'client-id-old-attribute-1',
                                'data': {
                                },
                                'id': '1',
                                'widget': '1',
                                'widgetType': 'TIME_RANGE'
                            }
                        ],
                        'clientId': 'entry-old-101 (UPDATED)',
                        'droppedExcerpt': 'This is a dropped text (UPDATED)',
                        'entryAttachment': None,
                        'entryType': 'EXCERPT',
                        'excerpt': 'This is a text (UPDATED)',
                        'highlightHidden': False,
                        'id': '2',
                        'image': {
                            'id': '2',
                            'title': 'file-1'
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
                                'widgetType': 'TIME_RANGE'
                            }
                        ],
                        'clientId': 'entry-new-102',
                        'droppedExcerpt': 'This is a dropped text (NEW)',
                        'entryAttachment': None,
                        'entryType': 'EXCERPT',
                        'excerpt': 'This is a text (NEW)',
                        'highlightHidden': False,
                        'id': '3',
                        'image': {
                            'id': '2',
                            'title': 'file-1'
                        },
                        'informationDate': '2021-01-01',
                        'order': 1
                    }
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
                                'id': '4',
                                'widget': '1',
                                'widgetType': 'TIME_RANGE'
                            },
                            {
                                'clientId': 'client-id-old-attribute-1',
                                'data': {
                                },
                                'id': '1',
                                'widget': '1',
                                'widgetType': 'TIME_RANGE'
                            }
                        ],
                        'clientId': 'entry-old-101 (UPDATED)',
                        'droppedExcerpt': 'This is a dropped text (UPDATED)',
                        'entryAttachment': None,
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
                                'id': '5',
                                'widget': '1',
                                'widgetType': 'TIME_RANGE'
                            }
                        ],
                        'clientId': 'entry-new-102',
                        'droppedExcerpt': 'This is a dropped text (NEW)',
                        'entryAttachment': None,
                        'entryType': 'EXCERPT',
                        'excerpt': 'This is a text (NEW)',
                        'highlightHidden': False,
                        'id': '4',
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
                    'entryAttachment': None,
                    'entryType': 'EXCERPT',
                    'excerpt': 'This is a text',
                    'highlightHidden': False,
                    'id': '1',
                    'image': {
                        'id': '2',
                        'title': 'file-1'
                    },
                    'informationDate': '2021-01-01',
                    'order': 1
                }
            }
        }
    }
}

snapshots['TestEntryMutation::test_entry_create lead-preview-attachment-success'] = {
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
                            'id': '7',
                            'widget': '1',
                            'widgetType': 'TIME_RANGE'
                        },
                        {
                            'clientId': 'client-id-attribute-2',
                            'data': {
                            },
                            'id': '8',
                            'widget': '2',
                            'widgetType': 'TIME'
                        },
                        {
                            'clientId': 'client-id-attribute-3',
                            'data': {
                            },
                            'id': '9',
                            'widget': '3',
                            'widgetType': 'GEO'
                        }
                    ],
                    'clientId': 'entry-101',
                    'droppedExcerpt': 'This is a dropped text',
                    'entryAttachment': {
                        'entryFileType': 'IMAGE',
                        'file': {
                            'name': 'entry/attachment/example_1_1.png',
                            'url': 'http://testserver/media/entry/attachment/example_1_1.png'
                        },
                        'filePreview': {
                            'name': 'entry/attachment/example_1_1.png',
                            'url': 'http://testserver/media/entry/attachment/example_1_1.png'
                        },
                        'id': '1',
                        'leadAttachmentId': '1'
                    },
                    'entryType': 'ATTACHMENT',
                    'excerpt': '',
                    'highlightHidden': False,
                    'id': '3',
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
                            'id': '4',
                            'widget': '1',
                            'widgetType': 'TIME_RANGE'
                        },
                        {
                            'clientId': 'client-id-attribute-2',
                            'data': {
                            },
                            'id': '5',
                            'widget': '2',
                            'widgetType': 'TIME'
                        },
                        {
                            'clientId': 'client-id-attribute-3',
                            'data': {
                            },
                            'id': '6',
                            'widget': '3',
                            'widgetType': 'GEO'
                        }
                    ],
                    'clientId': 'entry-101',
                    'droppedExcerpt': 'This is a dropped text',
                    'entryAttachment': None,
                    'entryType': 'EXCERPT',
                    'excerpt': 'This is a text',
                    'highlightHidden': False,
                    'id': '2',
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
                            'widgetType': 'TIME_RANGE'
                        },
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
                        }
                    ],
                    'clientId': 'entry-101',
                    'droppedExcerpt': 'This is a dropped text',
                    'entryType': 'EXCERPT',
                    'excerpt': 'This is a text',
                    'highlightHidden': False,
                    'id': '1',
                    'image': {
                        'id': '2',
                        'title': 'file-1'
                    },
                    'informationDate': '2021-01-01',
                    'order': 1
                }
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
                            'id': '6',
                            'widget': '1',
                            'widgetType': 'TIME_RANGE'
                        },
                        {
                            'clientId': 'client-id-attribute-1',
                            'data': {
                            },
                            'id': '4',
                            'widget': '1',
                            'widgetType': 'TIME_RANGE'
                        },
                        {
                            'clientId': 'client-id-attribute-2',
                            'data': {
                            },
                            'id': '5',
                            'widget': '2',
                            'widgetType': 'TIME'
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
