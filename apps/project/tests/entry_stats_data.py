WIDGET_DATA = {
}


# NOTE: This structure and value are set through https://github.com/the-deep/client
WIDGET_DATA = {
    'multiselectWidget': {
        'options': [
            {'key': 'option-1', 'label': 'Option 1'},
            {'key': 'option-2', 'label': 'Option 2'},
            {'key': 'option-3', 'label': 'Option 3'}
        ]
    },
    'scaleWidget': {
        'scale_units': [
            {'key': 'scale-1', 'color': '#470000', 'label': 'Scale 1'},
            {'key': 'scale-2', 'color': '#a40000', 'label': 'Scale 2'},
            {'key': 'scale-3', 'color': '#d40000', 'label': 'Scale 3'}
        ]
    },

    'matrix1dWidget': {
        'rows': [
            {
                'key': 'pillar-1',
                'cells': [
                    {'key': 'subpillar-1', 'value': 'Politics'},
                    {'key': 'subpillar-2', 'value': 'Security'},
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

    'geoWidget': {},
}

# NOTE: This structure and value are set through https://github.com/the-deep/client
ATTRIBUTE_DATA = {
    'geoWidget': {},

    'multiselectWidget': {
        'data': {'value': ['option-3', 'option-1']},
    },

    'scaleWidget': {
        'data': {'value': 'scale-1'},
    },

    'matrix1dWidget': {
        'data': {
            'value': {
                'pillar-2': {'subpillar-8': True},
                'pillar-1': {'subpillar-7': False},
                'pillar-4': {'subpillar-18': True},
            },
        },
    },

    'matrix2dWidget': {
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
    },

    'conditionalWidget': {
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
    },
}
