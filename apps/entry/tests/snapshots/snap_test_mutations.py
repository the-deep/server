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
                        'excerpt': 'HChpoevbLJoLoaeTOdoecveGprQFnIiUKKEpYEZAmggQBwBADUdRPPgdzUvZgpmmICiBlrDpeCZJgdPIafWpkAFEnzdkyayqYYDs',
                        'highlightHidden': False,
                        'id': '1',
                        'image': {
                            'id': '5',
                            'title': 'file-4'
                        },
                        'informationDate': None,
                        'order': 1
                    }
                ],
                'errors': [
                    None,
                    [
                        {
                            'arrayErrors': None,
                            'clientId': 'entry-new-102',
                            'field': 'leadAttachment',
                            'messages': "You don't have permission to attach lead attachment: Image extracted for 2",
                            'objectErrors': None
                        }
                    ],
                    [
                        {
                            'arrayErrors': None,
                            'clientId': 'entry-new-103',
                            'field': 'leadAttachment',
                            'messages': 'LeadPreviewAttachment is required with entry_tag is attachment',
                            'objectErrors': None
                        }
                    ]
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
                                'widgetType': 'MATRIX1D'
                            },
                            {
                                'clientId': 'client-id-old-attribute-1',
                                'data': {
                                },
                                'id': '1',
                                'widget': '1',
                                'widgetType': 'MATRIX1D'
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
                            'id': '6',
                            'title': 'file-5'
                        },
                        'informationDate': '2021-01-01',
                        'order': 1
                    },
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
                    [
                        {
                            'arrayErrors': None,
                            'clientId': 'entry-new-102',
                            'field': 'leadAttachment',
                            'messages': "You don't have permission to attach lead attachment: Image extracted for 2",
                            'objectErrors': None
                        }
                    ],
                    [
                        {
                            'arrayErrors': None,
                            'clientId': 'entry-new-103',
                            'field': 'leadAttachment',
                            'messages': 'LeadPreviewAttachment is required with entry_tag is attachment',
                            'objectErrors': None
                        }
                    ]
                ],
                'result': [
                    {
                        'attributes': [
                            {
                                'clientId': 'client-id-old-new-attribute-1',
                                'data': {
                                },
                                'id': '3',
                                'widget': '1',
                                'widgetType': 'MATRIX1D'
                            },
                            {
                                'clientId': 'client-id-old-attribute-1',
                                'data': {
                                },
                                'id': '1',
                                'widget': '1',
                                'widgetType': 'MATRIX1D'
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
                            'id': '6',
                            'title': 'file-5'
                        },
                        'informationDate': '2021-01-01',
                        'order': 1
                    },
                    None,
                    None
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
                            'widgetType': 'MATRIX1D'
                        },
                        {
                            'clientId': 'client-id-attribute-2',
                            'data': {
                            },
                            'id': '2',
                            'widget': '2',
                            'widgetType': 'MATRIX1D'
                        },
                        {
                            'clientId': 'client-id-attribute-3',
                            'data': {
                            },
                            'id': '3',
                            'widget': '3',
                            'widgetType': 'SCALE'
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
                            'widgetType': 'MATRIX1D'
                        },
                        {
                            'clientId': 'client-id-attribute-2',
                            'data': {
                            },
                            'id': '8',
                            'widget': '2',
                            'widgetType': 'MATRIX1D'
                        },
                        {
                            'clientId': 'client-id-attribute-3',
                            'data': {
                            },
                            'id': '9',
                            'widget': '3',
                            'widgetType': 'SCALE'
                        }
                    ],
                    'clientId': 'entry-101',
                    'droppedExcerpt': 'This is a dropped text',
                    'entryAttachment': {
                        'entryFileType': 'IMAGE',
                        'file': {
                            'name': 'entry/attachment/example_1_2.png',
                            'url': 'http://testserver/media/entry/attachment/example_1_2.png'
                        },
                        'filePreview': {
                            'name': 'entry/attachment/example_1_2.png',
                            'url': 'http://testserver/media/entry/attachment/example_1_2.png'
                        },
                        'id': '1',
                        'leadAttachmentId': '1'
                    },
                    'entryType': 'ATTACHMENT',
                    'excerpt': '',
                    'highlightHidden': False,
                    'id': '3',
                    'image': None,
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
                            'widgetType': 'MATRIX1D'
                        },
                        {
                            'clientId': 'client-id-attribute-2',
                            'data': {
                            },
                            'id': '5',
                            'widget': '2',
                            'widgetType': 'MATRIX1D'
                        },
                        {
                            'clientId': 'client-id-attribute-3',
                            'data': {
                            },
                            'id': '6',
                            'widget': '3',
                            'widgetType': 'SCALE'
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
                        'id': '4',
                        'title': 'file-3'
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
                            'widgetType': 'MATRIX1D'
                        },
                        {
                            'clientId': 'client-id-attribute-1',
                            'data': {
                            },
                            'id': '1',
                            'widget': '1',
                            'widgetType': 'MATRIX1D'
                        },
                        {
                            'clientId': 'client-id-attribute-2',
                            'data': {
                            },
                            'id': '2',
                            'widget': '2',
                            'widgetType': 'MATRIX1D'
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
                            'widgetType': 'MATRIX1D'
                        },
                        {
                            'clientId': 'client-id-attribute-1',
                            'data': {
                            },
                            'id': '4',
                            'widget': '1',
                            'widgetType': 'MATRIX1D'
                        },
                        {
                            'clientId': 'client-id-attribute-2',
                            'data': {
                            },
                            'id': '5',
                            'widget': '2',
                            'widgetType': 'MATRIX1D'
                        }
                    ],
                    'clientId': 'entry-101',
                    'droppedExcerpt': 'This is a dropped text',
                    'entryType': 'EXCERPT',
                    'excerpt': 'This is a text',
                    'highlightHidden': False,
                    'id': '1',
                    'image': {
                        'id': '4',
                        'title': 'file-3'
                    },
                    'informationDate': '2021-01-01',
                    'order': 1
                }
            }
        }
    }
}
