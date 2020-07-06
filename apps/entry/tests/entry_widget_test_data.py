# NOTE: This structure and value are set through https://github.com/the-deep/client
WIDGET_DATA = {
    'selectWidget': {
        'title': 'My Select',
        'options': [
            {'key': 'option-1', 'label': 'Option 1'},
            {'key': 'option-2', 'label': 'Option 2'},
            {'key': 'option-3', 'label': 'Option 3'}
        ]
    },
    'multiselectWidget': {
        'title': 'My Multi Select',
        'options': [
            {'key': 'option-1', 'label': 'Option 1'},
            {'key': 'option-2', 'label': 'Option 2'},
            {'key': 'option-3', 'label': 'Option 3'}
        ]
    },
    'scaleWidget': {
        'title': 'My Scale',
        'default_scale_unit': 'scale-1',
        'scale_units': [
            {'key': 'scale-1', 'color': '#470000', 'label': 'Scale 1'},
            {'key': 'scale-2', 'color': '#a40000', 'label': 'Scale 2'},
            {'key': 'scale-3', 'color': '#d40000', 'label': 'Scale 3'}
        ]
    },
    'numberMatrixWidget': {
        'title': 'My Number Matrix',
        'row_headers': [
            {'key': 'row-1', 'title': 'Row 1'},
            {'key': 'row-2', 'title': 'Row 2'},
            {'key': 'row-3', 'title': 'Row 3'},
        ],
        'column_headers': [
            {'key': 'col-1', 'title': 'Col 1'},
            {'key': 'col-2', 'title': 'Col 2'},
            {'key': 'col-3', 'title': 'Col 3'},
        ],
    },
    'organigramWidget': {
        'key': 'base',
        'title': 'Base Node',
        'organs': [{
            'key': 'node-1',
            'title': 'Node 1',
            'organs': [{
                'key': 'node-2',
                'title': 'Node 2',
                'organs': [
                    {'key': 'node-3', 'title': 'Node 3', 'organs': []},
                    {'key': 'node-4', 'title': 'Node 4', 'organs': []},
                    {'key': 'node-5', 'title': 'Node 5', 'organs': []},
                    {
                        'key': 'node-6',
                        'title': 'Node 6',
                        'organs': [{
                            'key': 'node-7',
                            'title': 'Node 7',
                            'organs': [
                                {'key': 'node-8', 'title': 'Node 8', 'organs': []}
                            ]
                        }]
                    }
                ]
            }]
        }]
    },

    'matrix1dWidget': {
        'title': 'My Matrix1d',
        'rows': [
            {
                'key': 'pillar-1',
                'cells': [
                    {'key': 'subpillar-1', 'value': 'Politics', 'tooltip': ''},
                    {'key': 'subpillar-2', 'value': 'Security', 'tooltip': 'Secure is good'},
                    {'key': 'subpillar-3', 'value': 'Legal  & Policy'},
                    {'key': 'subpillar-4', 'value': 'Demography'},
                    {'key': 'subpillar-5', 'value': 'Economy'},
                    {'key': 'subpillar-5', 'value': 'Socio Cultural'},
                    {'key': 'subpillar-7', 'value': 'Environment'},
                ],
                'color': '#c26b27',
                'title': 'Context',
                'tooltip': 'Information about the environment in which humanitarian actors operates and the crisis happen', # noqa E501
            }, {
                'key': 'pillar-2',
                'cells': [
                    {'key': 'subpillar-8', 'value': 'Affected Groups'},
                    {'key': 'subpillar-9', 'value': 'Population Movement'},
                    {'key': 'subpillar-10', 'value': 'Push/Pull Factors'},
                    {'key': 'subpillar-11', 'value': 'Casualties'},
                ],
                'color': '#efaf78',
                'title': 'Humanitarian Profile',
                'tooltip': 'Information related to the population affected, including affected residents and displaced people', # noqa E501
            }, {
                'key': 'pillar-3',
                'cells': [
                    {'key': 'subpillar-12', 'value': 'Relief to Beneficiaries'},
                    {'key': 'subpillar-13', 'value': 'Beneficiaries to Relief'},
                    {'key': 'subpillar-14', 'value': 'Physical Constraints'},
                    {'key': 'subpillar-15', 'value': 'Humanitarian Access Gaps'},
                ],
                'color': '#b9b2a5',
                'title': 'Humanitarian Access',
                'tooltip': 'Information related to restrictions and constraints in accessing or being accessed by people in need', # noqa E501
            }, {
                'key': 'pillar-4',
                'cells': [
                    {'key': 'subpillar-16', 'value': 'Communication Means & Channels'},
                    {'key': 'subpillar-17', 'value': 'Information Challenges'},
                    {'key': 'subpillar-18', 'value': 'Information Needs & Gaps'},
                ],
                'color': '#9bd65b',
                'title': 'Information',
                'tooltip': 'Information about information, including communication means, information challenges and information needs', # noqa E501
            }]
    },

    'matrix2dWidget': {
        'title': 'My Matrix2d',
        'sectors': [
            {'id': 'sector-9', 'title': 'Cross', 'tooltip': 'Cross sectoral information', 'subsectors': []},
            {'id': 'sector-0', 'title': 'Food', 'tooltip': '...', 'subsectors': []},
            {'id': 'sector-1', 'title': 'Livelihoods', 'tooltip': '...', 'subsectors': []},
            {'id': 'sector-2', 'title': 'Health', 'tooltip': '...', 'subsectors': []},
            {'id': 'sector-3', 'title': 'Nutrition', 'tooltip': '...', 'subsectors': []},
            {
                'id': 'sector-4',
                'title': 'WASH',
                'tooltip': '...',
                'subsectors': [
                    {'id': 'subsector-1', 'title': 'Water'},
                    {'id': 'subsector-2', 'title': 'Sanitation'},
                    {'id': 'subsector-3', 'title': 'Hygiene'},
                    {'id': 'subsector-4', 'title': 'Waste management', 'tooltip': ''},
                    {'id': 'subsector-5', 'title': 'Vector control', 'tooltip': ''}
                ]
            },
            {'id': 'sector-5', 'title': 'Shelter', 'tooltip': '...', 'subsectors': []},
            {
                'id': 'sector-7',
                'title': 'Education',
                'tooltip': '.....',
                'subsectors': [
                    {'id': 'subsector-6', 'title': 'Learning Environment', 'tooltip': ''},
                    {'id': 'subsector-7', 'title': 'Teaching and Learning', 'tooltip': ''},
                    {'id': 'subsector-8', 'title': 'Teachers and Education Personnel', 'tooltip': ''},
                ]
            },
            {'id': 'sector-8', 'title': 'Protection', 'tooltip': '', 'subsectors': []},
            {'id': 'sector-10', 'title': 'Agriculture', 'tooltip': '...', 'subsectors': []},
            {'id': 'sector-11', 'title': 'Logistics', 'tooltip': '...', 'subsectors': []}
        ],
        'dimensions': [
            {
                'id': 'dimension-0',
                'color': '#eae285',
                'title': 'Scope & Scale',
                'tooltip': 'Information about the direct and indirect impact of the disaster or crisis',
                'subdimensions': [
                    {'id': 'subdimension-0', 'title': 'Drivers/Aggravating Factors', 'tooltip': '...'},
                    {'id': 'subdimension-3', 'title': 'System Disruption', 'tooltip': '...'},
                    {'id': 'subdimension-4', 'title': 'Damages & Losses', 'tooltip': '...'},
                    {'id': 'subdimension-6', 'title': 'Lessons Learnt', 'tooltip': '...'}
                ]
            },
            {
                'id': 'dimension-1',
                'color': '#fba855',
                'title': 'Humanitarian Conditions',
                'tooltip': '...',
                'subdimensions': [
                    {'id': 'subdimension-1', 'title': 'Living Standards', 'tooltip': '...'},
                    {'id': 'us9kizxxwha7cpgb', 'title': 'Coping Mechanisms', 'tooltip': ''},
                    {'id': 'subdimension-7', 'title': 'Physical & mental wellbeing', 'tooltip': '..'},
                    {'id': 'subdimension-8', 'title': 'Risks & Vulnerabilities', 'tooltip': '...'},
                    {'id': 'ejve4vklgge9ysxm', 'title': 'People with Specific Needs', 'tooltip': ''},
                    {'id': 'subdimension-10', 'title': 'Unmet Needs', 'tooltip': '...'},
                    {'id': 'subdimension-16', 'title': 'Lessons Learnt', 'tooltip': '...'},
                ]
            },
            {
                'id': 'dimension-2',
                'color': '#92c5f6',
                'title': 'Capacities & Response',
                'tooltip': '...',
                'subdimensions': [
                    {'id': '7iiastsikxackbrt', 'title': 'System Functionality', 'tooltip': '...'},
                    {'id': 'subdimension-11', 'title': 'Government', 'tooltip': '...'},
                    {'id': 'drk4j92jwvmck7dc', 'title': 'LNGO', 'tooltip': '...'},
                    {'id': 'subdimension-12', 'title': 'International', 'tooltip': '...'},
                    {'id': 'subdimension-14', 'title': 'Response Gaps', 'tooltip': '...'},
                    {'id': 'subdimension-15', 'title': 'Lessons Learnt', 'tooltip': '...'},
                ]
            }
        ]
    },

    'conditionalWidget': {
        'widgets': [{
            'widget': {
                'key': 'scalewidget-1',
                'title': 'Severity',
                'widget_id': 'scaleWidget',
                'properties': {
                    'data': {
                        'scale_units': [
                            {'key': 'scale-1', 'color': '#fef0d9', 'label': 'No problem/Minor Problem'},
                            {'key': 'scale-2', 'color': '#fdcc8a', 'label': 'Of Concern'},
                            {'key': 'scale-3', 'color': '#fc8d59', 'label': 'Major'},
                            {'key': 'scale-4', 'color': '#e34a33', 'label': 'Severe'},
                            {'key': 'scale-5', 'color': '#b30000', 'label': 'Critical'},
                        ],
                    }
                }
            },
            'conditions': {
                'list': [{}],
                'operator': 'AND',
            }
        }]
    },

    'dateWidget': {
        'title': 'My Date',
        'information_date_selected': False,
    },
    'dateRangeWidget': {
        'title': 'My Date Range',
    },
    'timeWidget': {
        'title': 'My Time',
    },
    'timeRangeWidget': {
        'title': 'My Time Range',
    },
    'numberWidget': {
        'title': 'My Number',
        'maxValue': 0,
        'minvalue': 12,
    },
    'textWidget': {
        'title': 'My Text',
    },
}

# NOTE: This structure and value are set through https://github.com/the-deep/client
# c_response is for comprehensive API widget response
ATTRIBUTE_DATA = {
    'selectWidget': [{
        'data': {'value': 'option-3'},
        'c_response': 'Option 3',
    }, {
        'data': {'value': 'option-5'},
        'c_response': None,
    }],

    'multiselectWidget': [{
        'data': {'value': ['option-3', 'option-1']},
        'c_response': ['Option 3', 'Option 1'],
    }, {
        'data': {'value': ['option-5', 'option-1']},
        'c_response': ['Option 1'],
    }],

    'scaleWidget': [{
        'data': {'value': 'scale-1'},
        'c_response': {
            'min': {'key': 'scale-1', 'color': '#470000', 'label': 'Scale 1'},
            'max': {'key': 'scale-3', 'color': '#d40000', 'label': 'Scale 3'},
            'label': 'Scale 1',
            'index': 1,
        },
    }, {
        'data': {'value': 'scale-5'},
        'c_response': {
            'min': {'key': 'scale-1', 'color': '#470000', 'label': 'Scale 1'},
            'max': {'key': 'scale-3', 'color': '#d40000', 'label': 'Scale 3'},
            'label': None,
            'index': None,
        },
    }],

    'dateWidget': [{
        'data': {'value': '2019-06-25'},
        'c_response': '25-06-2019',
    }, {
        'data': {'value': None},
        'c_response': None,
    }],

    'dateRangeWidget': [{
        'data': {'value': {'from': '2012-06-25', 'to': '2019-06-22'}},
        'c_response': {
            'from': '25-06-2012',
            'to': '22-06-2019',
        },
    }],

    'timeWidget': [{
        'data': {'value': '22:34:00'},
        'c_response': '22:34',
    }, {
        'data': {'value': None},
        'c_response': None,
    }],

    'numberWidget': [{
        'data': {'value': '12'},
        'c_response': '12',
    }, {
        'data': {'value': None},
        'c_response': None,
    }],

    'textWidget': [{
        'data': {'value': 'This is a sample text'},
        'c_response': 'This is a sample text',
    }, {
        'data': {'value': None},
        'c_response': '',
    }],

    'numberMatrixWidget': [{
        'data': {
            'value': {
                'row-3': {
                    'col-3': 12312,
                    'col-1': 123,
                },
                'row-2': {
                    'col-2': 123,
                },
            },
        },
        'c_response': [{
            'value': 12312,
            'row': {'id': 'row-3', 'title': 'Row 3'},
            'column': {'id': 'col-3', 'title': 'Col 3'},
        }, {
            'value': 123,
            'row': {'id': 'row-3', 'title': 'Row 3'},
            'column': {'id': 'col-1', 'title': 'Col 1'},
        }, {
            'value': 123,
            'row': {'id': 'row-2', 'title': 'Row 2'},
            'column': {'id': 'col-2', 'title': 'Col 2'},
        }],
    }, {
        'data': {
            'value': {
                'row-3': {
                    'col-3': 12312,
                    'col-9': 123,
                },
                'row-2': {
                    'col-10': 123,
                },
            },
        },
        'c_response': [{
            'value': 12312,
            'row': {'id': 'row-3', 'title': 'Row 3'},
            'column': {'id': 'col-3', 'title': 'Col 3'},
        }],
    }],

    'matrix1dWidget': [{
        'data': {
            'value': {
                'pillar-2': {'subpillar-8': True},
                'pillar-1': {'subpillar-7': False},
                'pillar-4': {'subpillar-18': True},
            },
        },
        'c_response': [{
            'id': 'subpillar-8',
            'value': 'Affected Groups',
            'row': {
                'id': 'pillar-2',
                'title': 'Humanitarian Profile',
            },
        }, {
            'id': 'subpillar-18',
            'value': 'Information Needs & Gaps',
            'row': {
                'id': 'pillar-4',
                'title': 'Information',
            },
        }],
    }, {
        'data': {
            'value': {
                'pillar-2': {'subpillar-8': True},
                'pillar-1': {'subpillar-12': False},
                'pillar-4': {'subpillar-122': True},
            },
        },
        'c_response': [{
            'id': 'subpillar-8',
            'value': 'Affected Groups',
            'row': {
                'id': 'pillar-2',
                'title': 'Humanitarian Profile',
            },
        }],
    }],

    'matrix2dWidget': [{
        'data': {
            'value': {
                'dimension-0': {
                    'subdimension-4': {
                        'sector-1': [],
                        'sector-4': ['subsector-2', 'subsector-4'],
                        'sector-7': ['subsector-8', 'subsector-6']
                    }
                }
            },
        },
        'c_response': [{
            'dimension': {'id': 'dimension-0', 'title': 'Scope & Scale'},
            'subdimension': {'id': 'subdimension-4', 'title': 'Damages & Losses'},
            'sector': {'id': 'sector-1', 'title': 'Livelihoods'},
            'subsectors': []
        }, {
            'dimension': {'id': 'dimension-0', 'title': 'Scope & Scale'},
            'subdimension': {'id': 'subdimension-4', 'title': 'Damages & Losses'},
            'sector': {'id': 'sector-4', 'title': 'WASH'},
            'subsectors': [
                {'id': 'subsector-2', 'title': 'Sanitation'},
                {'id': 'subsector-4', 'title': 'Waste management'}
            ]
        }, {
            'dimension': {'id': 'dimension-0', 'title': 'Scope & Scale'},
            'subdimension': {'id': 'subdimension-4', 'title': 'Damages & Losses'},
            'sector': {'id': 'sector-7', 'title': 'Education'},
            'subsectors': [
                {'id': 'subsector-8', 'title': 'Teachers and Education Personnel'},
                {'id': 'subsector-6', 'title': 'Learning Environment'}
            ]
        }],
    }, {
        'data': {
            'value': {
                'dimension-0': {
                    'subdimension-4': {
                        'sector-1': [],
                        'sector-4': ['subsector-10', 'subsector-4'],
                        'sector-7': ['subsector-4', 'subsector-122']
                    }
                },
                'dimension-1': {
                    'subdimension-9': {
                        'sector-1': [],
                    }
                },
            },
        },
        'c_response': [{
            'dimension': {'id': 'dimension-0', 'title': 'Scope & Scale'},
            'subdimension': {'id': 'subdimension-4', 'title': 'Damages & Losses'},
            'sector': {'id': 'sector-1', 'title': 'Livelihoods'},
            'subsectors': []
        }, {
            'dimension': {'id': 'dimension-0', 'title': 'Scope & Scale'},
            'subdimension': {'id': 'subdimension-4', 'title': 'Damages & Losses'},
            'sector': {'id': 'sector-4', 'title': 'WASH'},
            'subsectors': [
                {'id': 'subsector-4', 'title': 'Waste management'}
            ]
        }, {
            'dimension': {'id': 'dimension-0', 'title': 'Scope & Scale'},
            'subdimension': {'id': 'subdimension-4', 'title': 'Damages & Losses'},
            'sector': {'id': 'sector-7', 'title': 'Education'},
            'subsectors': []
        }],
    }],

    'timeRangeWidget': [{
        'data': {'value': {'from': '18:05:00', 'to': '23:05:00'}},
        'c_response': {
            'from': '18:05',
            'to': '23:05',
        },
    }],

    'organigramWidget': [{
        'data': {'value': ['node-1', 'node-8']},
        'c_response': [{
            'key': 'node-1',
            'title': 'Node 1',
            'parents': [{'key': 'base', 'title': 'Base Node'}],
        }, {
            'key': 'node-8',
            'title': 'Node 8',
            'parents': [
                {'key': 'node-7', 'title': 'Node 7'},
                {'key': 'node-6', 'title': 'Node 6'},
                {'key': 'node-2', 'title': 'Node 2'},
                {'key': 'node-1', 'title': 'Node 1'},
                {'key': 'base', 'title': 'Base Node'},
            ]
        }],
    }, {
        'data': {'value': ['node-1', 'node-9', 'base']},
        'c_response': [{
            'key': 'base',
            'title': 'Base Node',
            'parents': [],
        }, {
            'key': 'node-1',
            'title': 'Node 1',
            'parents': [{'key': 'base', 'title': 'Base Node'}],
        }],
    }],

    'conditionalWidget': [{
        'data': {
            'value': {
                'selected_widget_key': 'scalewidget-1',
                'scalewidget-1': {
                    'data': {
                        'value': 'scale-3',
                    }
                }
            }
        },
        'c_response': {
            'id': 'scalewidget-1',
            'type': 'scaleWidget',
            'title': 'Severity',
            'value': {
                'max': {'key': 'scale-5', 'color': '#b30000', 'label': 'Critical'},
                'min': {'key': 'scale-1', 'color': '#fef0d9', 'label': 'No problem/Minor Problem'},
                'label': 'Major',
                'index': 3,
            },
        },
    }, {
        'data': {
            'value': {
                'selected_widget_key': 'scalewidget-2',
                'scalewidget-1': {
                    'data': {
                        'value': 'scale-3',
                    }
                }
            }
        },
        'c_response': None,
    }],
}
