# NOTE: This structure and value are set through https://github.com/the-deep/client
WIDGET_PROPERTIES = {
    'selectWidget': {
        'options': [
            {'clientId': 'option-1', 'label': 'Option 1'},
            {'clientId': 'option-2', 'label': 'Option 2'},
            {'clientId': 'option-3', 'label': 'Option 3'}
        ]
    },
    'multiselectWidget': {
        'options': [
            {'clientId': 'option-1', 'label': 'Option 1'},
            {'clientId': 'option-2', 'label': 'Option 2'},
            {'clientId': 'option-3', 'label': 'Option 3'}
        ]
    },
    'scaleWidget': {
        'defaultValue': 'scale-1',
        'options': [
            {'clientId': 'scale-1', 'color': '#470000', 'label': 'Scale 1'},
            {'clientId': 'scale-2', 'color': '#a40000', 'label': 'Scale 2'},
            {'clientId': 'scale-3', 'color': '#d40000', 'label': 'Scale 3'}
        ]
    },
    'organigramWidget': {
        'clientId': 'base',
        'label': 'Base Node',
        'children': [{
            'clientId': 'node-1',
            'label': 'Node 1',
            'children': [{
                'clientId': 'node-2',
                'label': 'Node 2',
                'children': [
                    {'clientId': 'node-3', 'label': 'Node 3', 'children': []},
                    {'clientId': 'node-4', 'label': 'Node 4', 'children': []},
                    {'clientId': 'node-5', 'label': 'Node 5', 'children': []},
                    {
                        'clientId': 'node-6',
                        'label': 'Node 6',
                        'children': [{
                            'clientId': 'node-7',
                            'label': 'Node 7',
                            'children': [
                                {'clientId': 'node-8', 'label': 'Node 8', 'children': []}
                            ]
                        }]
                    }
                ]
            }]
        }]
    },

    'matrix1dWidget': {
        'rows': [
            {
                'clientId': 'pillar-1',
                'cells': [
                    {'clientId': 'subpillar-1', 'label': 'Politics', 'tooltip': ''},
                    {'clientId': 'subpillar-2', 'label': 'Security', 'tooltip': 'Secure is good'},
                    {'clientId': 'subpillar-3', 'label': 'Legal  & Policy'},
                    {'clientId': 'subpillar-4', 'label': 'Demography'},
                    {'clientId': 'subpillar-5', 'label': 'Economy'},
                    {'clientId': 'subpillar-5', 'label': 'Socio Cultural'},
                    {'clientId': 'subpillar-7', 'label': 'Environment'},
                ],
                'color': '#c26b27',
                'label': 'Context',
                'tooltip': 'Information about the environment in which humanitarian actors operates and the crisis happen', # noqa E501
            }, {
                'clientId': 'pillar-2',
                'cells': [
                    {'clientId': 'subpillar-8', 'label': 'Affected Groups'},
                    {'clientId': 'subpillar-9', 'label': 'Population Movement'},
                    {'clientId': 'subpillar-10', 'label': 'Push/Pull Factors'},
                    {'clientId': 'subpillar-11', 'label': 'Casualties'},
                ],
                'color': '#efaf78',
                'label': 'Humanitarian Profile',
                'tooltip': 'Information related to the population affected, including affected residents and displaced people', # noqa E501
            }, {
                'clientId': 'pillar-3',
                'cells': [
                    {'clientId': 'subpillar-12', 'label': 'Relief to Beneficiaries'},
                    {'clientId': 'subpillar-13', 'label': 'Beneficiaries to Relief'},
                    {'clientId': 'subpillar-14', 'label': 'Physical Constraints'},
                    {'clientId': 'subpillar-15', 'label': 'Humanitarian Access Gaps'},
                ],
                'color': '#b9b2a5',
                'label': 'Humanitarian Access',
                'tooltip': 'Information related to restrictions and constraints in accessing or being accessed by people in need', # noqa E501
            }, {
                'clientId': 'pillar-4',
                'cells': [
                    {'clientId': 'subpillar-16', 'label': 'Communication Means & Channels'},
                    {'clientId': 'subpillar-17', 'label': 'Information Challenges'},
                    {'clientId': 'subpillar-18', 'label': 'Information Needs & Gaps'},
                ],
                'color': '#9bd65b',
                'label': 'Information',
                'tooltip': 'Information about information, including communication means, information challenges and information needs', # noqa E501
            }]
    },

    'matrix2dWidget': {
        'columns': [
            {'clientId': 'sector-9', 'label': 'Cross', 'tooltip': 'Cross sectoral information', 'subColumns': []},
            {'clientId': 'sector-0', 'label': 'Food', 'tooltip': '...', 'subColumns': []},
            {'clientId': 'sector-1', 'label': 'Livelihoods', 'tooltip': '...', 'subColumns': []},
            {'clientId': 'sector-2', 'label': 'Health', 'tooltip': '...', 'subColumns': []},
            {'clientId': 'sector-3', 'label': 'Nutrition', 'tooltip': '...', 'subColumns': []},
            {
                'clientId': 'sector-4',
                'label': 'WASH',
                'tooltip': '...',
                'subColumns': [
                    {'clientId': 'subsector-1', 'label': 'Water'},
                    {'clientId': 'subsector-2', 'label': 'Sanitation'},
                    {'clientId': 'subsector-3', 'label': 'Hygiene'},
                    {'clientId': 'subsector-4', 'label': 'Waste management', 'tooltip': ''},
                    {'clientId': 'subsector-5', 'label': 'Vector control', 'tooltip': ''}
                ]
            },
            {'clientId': 'sector-5', 'label': 'Shelter', 'tooltip': '...', 'subColumns': []},
            {
                'clientId': 'sector-7',
                'label': 'Education',
                'tooltip': '.....',
                'subColumns': [
                    {'clientId': 'subsector-6', 'label': 'Learning Environment', 'tooltip': ''},
                    {'clientId': 'subsector-7', 'label': 'Teaching and Learning', 'tooltip': ''},
                    {'clientId': 'subsector-8', 'label': 'Teachers and Education Personnel', 'tooltip': ''},
                ]
            },
            {'clientId': 'sector-8', 'label': 'Protection', 'tooltip': '', 'subColumns': []},
            {'clientId': 'sector-10', 'label': 'Agriculture', 'tooltip': '...', 'subColumns': []},
            {'clientId': 'sector-11', 'label': 'Logistics', 'tooltip': '...', 'subColumns': []}
        ],
        'rows': [
            {
                'clientId': 'dimension-0',
                'color': '#eae285',
                'label': 'Scope & Scale',
                'tooltip': 'Information about the direct and indirect impact of the disaster or crisis',
                'subRows': [
                    {'clientId': 'subdimension-0', 'label': 'Drivers/Aggravating Factors', 'tooltip': '...'},
                    {'clientId': 'subdimension-3', 'label': 'System Disruption', 'tooltip': '...'},
                    {'clientId': 'subdimension-4', 'label': 'Damages & Losses', 'tooltip': '...'},
                    {'clientId': 'subdimension-6', 'label': 'Lessons Learnt', 'tooltip': '...'}
                ]
            },
            {
                'clientId': 'dimension-1',
                'color': '#fba855',
                'label': 'Humanitarian Conditions',
                'tooltip': '...',
                'subRows': [
                    {'clientId': 'subdimension-1', 'label': 'Living Standards', 'tooltip': '...'},
                    {'clientId': 'us9kizxxwha7cpgb', 'label': 'Coping Mechanisms', 'tooltip': ''},
                    {'clientId': 'subdimension-7', 'label': 'Physical & mental wellbeing', 'tooltip': '..'},
                    {'clientId': 'subdimension-8', 'label': 'Risks & Vulnerabilities', 'tooltip': '...'},
                    {'clientId': 'ejve4vklgge9ysxm', 'label': 'People with Specific Needs', 'tooltip': ''},
                    {'clientId': 'subdimension-10', 'label': 'Unmet Needs', 'tooltip': '...'},
                    {'clientId': 'subdimension-16', 'label': 'Lessons Learnt', 'tooltip': '...'},
                ]
            },
            {
                'clientId': 'dimension-2',
                'color': '#92c5f6',
                'label': 'Capacities & Response',
                'tooltip': '...',
                'subRows': [
                    {'clientId': '7iiastsikxackbrt', 'label': 'System Functionality', 'tooltip': '...'},
                    {'clientId': 'subdimension-11', 'label': 'Government', 'tooltip': '...'},
                    {'clientId': 'drk4j92jwvmck7dc', 'label': 'LNGO', 'tooltip': '...'},
                    {'clientId': 'subdimension-12', 'label': 'International', 'tooltip': '...'},
                    {'clientId': 'subdimension-14', 'label': 'Response Gaps', 'tooltip': '...'},
                    {'clientId': 'subdimension-15', 'label': 'Lessons Learnt', 'tooltip': '...'},
                ]
            }
        ]
    },

    'dateWidget': {
        'information_date_selected': False,
    },
    'numberWidget': {
        'maxValue': 0,
        'minvalue': 12,
    },
    'dateRangeWidget': {},
    'timeWidget': {},
    'timeRangeWidget': {},
    'textWidget': {},
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
        'data': {'value': {'startDate': '2012-06-25', 'endDate': '2019-06-22'}},
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
        'data': {'value': {'startTime': '18:05:00', 'endTime': '23:05:00'}},
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
}
