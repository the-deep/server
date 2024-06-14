WIDGET_DATA = {}


# NOTE: This structure and value are set through https://github.com/the-deep/client
WIDGET_DATA = {
    "multiselectWidget": {
        "options": [
            {"key": "option-1", "label": "Option 1"},
            {"key": "option-2", "label": "Option 2"},
            {"key": "option-3", "label": "Option 3"},
        ]
    },
    "scaleWidget": {
        "options": [
            {"key": "scale-1", "color": "#470000", "label": "Scale 1"},
            {"key": "scale-2", "color": "#a40000", "label": "Scale 2"},
            {"key": "scale-3", "color": "#d40000", "label": "Scale 3"},
        ]
    },
    "matrix1dWidget": {
        "rows": [
            {
                "key": "pillar-1",
                "cells": [
                    {"key": "subpillar-1", "value": "Politics"},
                    {"key": "subpillar-2", "value": "Security"},
                    {"key": "subpillar-3", "value": "Legal  & Policy"},
                    {"key": "subpillar-4", "value": "Demography"},
                    {"key": "subpillar-5", "value": "Economy"},
                    {"key": "subpillar-5", "value": "Socio Cultural"},
                    {"key": "subpillar-7", "value": "Environment"},
                ],
                "color": "#c26b27",
                "label": "Context",
                "tooltip": "Information about the environment in which humanitarian actors operates and the crisis happen",  # noqa E501
            },
            {
                "key": "pillar-2",
                "cells": [
                    {"key": "subpillar-8", "value": "Affected Groups"},
                    {"key": "subpillar-9", "value": "Population Movement"},
                    {"key": "subpillar-10", "value": "Push/Pull Factors"},
                    {"key": "subpillar-11", "value": "Casualties"},
                ],
                "color": "#efaf78",
                "label": "Humanitarian Profile",
                "tooltip": "Information related to the population affected, including affected residents and displaced people",  # noqa E501
            },
            {
                "key": "pillar-3",
                "cells": [
                    {"key": "subpillar-12", "value": "Relief to Beneficiaries"},
                    {"key": "subpillar-13", "value": "Beneficiaries to Relief"},
                    {"key": "subpillar-14", "value": "Physical Constraints"},
                    {"key": "subpillar-15", "value": "Humanitarian Access Gaps"},
                ],
                "color": "#b9b2a5",
                "label": "Humanitarian Access",
                "tooltip": "Information related to restrictions and constraints in accessing or being accessed by people in need",  # noqa E501
            },
            {
                "key": "pillar-4",
                "cells": [
                    {"key": "subpillar-16", "value": "Communication Means & Channels"},
                    {"key": "subpillar-17", "value": "Information Challenges"},
                    {"key": "subpillar-18", "value": "Information Needs & Gaps"},
                ],
                "color": "#9bd65b",
                "label": "Information",
                "tooltip": "Information about information, including communication means, information challenges and information needs",  # noqa E501
            },
        ]
    },
    "matrix2dWidget": {
        "columns": [
            {"key": "sector-9", "label": "Cross", "tooltip": "Cross sectoral information", "subColumns": []},
            {"key": "sector-0", "label": "Food", "tooltip": "...", "subColumns": []},
            {"key": "sector-1", "label": "Livelihoods", "tooltip": "...", "subColumns": []},
            {"key": "sector-2", "label": "Health", "tooltip": "...", "subColumns": []},
            {"key": "sector-3", "label": "Nutrition", "tooltip": "...", "subColumns": []},
            {
                "key": "sector-4",
                "label": "WASH",
                "tooltip": "...",
                "subColumns": [
                    {"key": "subsector-1", "label": "Water"},
                    {"key": "subsector-2", "label": "Sanitation"},
                    {"key": "subsector-3", "label": "Hygiene"},
                    {"key": "subsector-4", "label": "Waste management", "tooltip": ""},
                    {"key": "subsector-5", "label": "Vector control", "tooltip": ""},
                ],
            },
            {"key": "sector-5", "label": "Shelter", "tooltip": "...", "subColumns": []},
            {
                "key": "sector-7",
                "label": "Education",
                "tooltip": ".....",
                "subColumns": [
                    {"key": "subsector-6", "label": "Learning Environment", "tooltip": ""},
                    {"key": "subsector-7", "label": "Teaching and Learning", "tooltip": ""},
                    {"key": "subsector-8", "label": "Teachers and Education Personnel", "tooltip": ""},
                ],
            },
            {"key": "sector-8", "label": "Protection", "tooltip": "", "subColumns": []},
            {"key": "sector-10", "label": "Agriculture", "tooltip": "...", "subColumns": []},
            {"key": "sector-11", "label": "Logistics", "tooltip": "...", "subColumns": []},
        ],
        "rows": [
            {
                "key": "dimension-0",
                "color": "#eae285",
                "label": "Scope & Scale",
                "tooltip": "Information about the direct and indirect impact of the disaster or crisis",
                "subRows": [
                    {"key": "subdimension-0", "label": "Drivers/Aggravating Factors", "tooltip": "..."},
                    {"key": "subdimension-3", "label": "System Disruption", "tooltip": "..."},
                    {"key": "subdimension-4", "label": "Damages & Losses", "tooltip": "..."},
                    {"key": "subdimension-6", "label": "Lessons Learnt", "tooltip": "..."},
                ],
            },
            {
                "key": "dimension-1",
                "color": "#fba855",
                "label": "Humanitarian Conditions",
                "tooltip": "...",
                "subRows": [
                    {"key": "subdimension-1", "label": "Living Standards", "tooltip": "..."},
                    {"key": "us9kizxxwha7cpgb", "label": "Coping Mechanisms", "tooltip": ""},
                    {"key": "subdimension-7", "label": "Physical & mental wellbeing", "tooltip": ".."},
                    {"key": "subdimension-8", "label": "Risks & Vulnerabilities", "tooltip": "..."},
                    {"key": "ejve4vklgge9ysxm", "label": "People with Specific Needs", "tooltip": ""},
                    {"key": "subdimension-10", "label": "Unmet Needs", "tooltip": "..."},
                    {"key": "subdimension-16", "label": "Lessons Learnt", "tooltip": "..."},
                ],
            },
            {
                "key": "dimension-2",
                "color": "#92c5f6",
                "label": "Capacities & Response",
                "tooltip": "...",
                "subRows": [
                    {"key": "7iiastsikxackbrt", "label": "System Functionality", "tooltip": "..."},
                    {"key": "subdimension-11", "label": "Government", "tooltip": "..."},
                    {"key": "drk4j92jwvmck7dc", "label": "LNGO", "tooltip": "..."},
                    {"key": "subdimension-12", "label": "International", "tooltip": "..."},
                    {"key": "subdimension-14", "label": "Response Gaps", "tooltip": "..."},
                    {"key": "subdimension-15", "label": "Lessons Learnt", "tooltip": "..."},
                ],
            },
        ],
    },
    "geoWidget": {},
}

# NOTE: This structure and value are set through https://github.com/the-deep/client
ATTRIBUTE_DATA = {
    "geoWidget": {},
    "multiselectWidget": {
        "data": {"value": ["option-3", "option-1"]},
    },
    "scaleWidget": {
        "data": {"value": "scale-1"},
    },
    "matrix1dWidget": {
        "data": {
            "value": {
                "pillar-2": {"subpillar-8": True},
                "pillar-1": {"subpillar-7": False},
                "pillar-4": {"subpillar-18": True},
            },
        },
    },
    "matrix2dWidget": {
        "data": {
            "value": {
                "dimension-0": {
                    "subdimension-4": {
                        "sector-1": [],
                        "sector-4": ["subsector-2", "subsector-4"],
                        "sector-7": ["subsector-8", "subsector-6"],
                    }
                }
            },
        },
    },
}
