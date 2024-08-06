# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot


snapshots = Snapshot()

snapshots['TestAssessmentRegistryMutationSnapShotTestCase::test_assessment_registry_update error'] = {
    'data': {
        'project': {
            'updateAssessmentRegistry': {
                'errors': [
                    {
                        'arrayErrors': None,
                        'clientId': None,
                        'field': 'lead',
                        'messages': 'Only Source from current Project are allowed',
                        'objectErrors': None
                    },
                    {
                        'arrayErrors': [
                            {
                                'clientId': 'nonMemberErrors',
                                'messages': 'Dublicate organization selected',
                                'objectErrors': None
                            }
                        ],
                        'clientId': None,
                        'field': 'stakeholders',
                        'messages': None,
                        'objectErrors': None
                    },
                    {
                        'arrayErrors': [
                            {
                                'clientId': 'nonMemberErrors',
                                'messages': 'Score ratings should have unique score types',
                                'objectErrors': None
                            }
                        ],
                        'clientId': None,
                        'field': 'scoreRatings',
                        'messages': None,
                        'objectErrors': None
                    },
                    {
                        'arrayErrors': [
                            {
                                'clientId': 'nonMemberErrors',
                                'messages': 'Score analytical density should have unique sectors',
                                'objectErrors': None
                            }
                        ],
                        'clientId': None,
                        'field': 'scoreAnalyticalDensity',
                        'messages': None,
                        'objectErrors': None
                    },
                    {
                        'arrayErrors': [
                            {
                                'clientId': 'nonMemberErrors',
                                'messages': 'Dublicate question selected',
                                'objectErrors': None
                            }
                        ],
                        'clientId': None,
                        'field': 'cna',
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

snapshots['TestAssessmentRegistryMutationSnapShotTestCase::test_assessment_registry_update success'] = {
    'data': {
        'project': {
            'updateAssessmentRegistry': {
                'errors': None,
                'ok': True,
                'result': {
                    'additionalDocumentComplete': True,
                    'additionalDocuments': [
                    ],
                    'affectedGroups': [
                        'ALL_AFFECTED'
                    ],
                    'bgCountries': [
                        {
                            'id': '1'
                        }
                    ],
                    'bgCrisisStartDate': '2019-07-03',
                    'bgCrisisType': 'LANDSLIDE',
                    'bgPreparedness': 'WITHOUT_PREPAREDNESS',
                    'cna': [
                        {
                            'answer': True,
                            'id': '1',
                            'question': {
                                'id': '1',
                                'question': 'test question',
                                'sector': 'RELEVANCE',
                                'sectorDisplay': 'Relevance',
                                'subSector': 'RELEVANCE',
                                'subSectorDisplay': 'Relevance'
                            }
                        }
                    ],
                    'cnaComplete': True,
                    'confidentiality': 'CONFIDENTIAL',
                    'confidentialityDisplay': 'Confidential',
                    'coordinatedJoint': 'HARMONIZED',
                    'coordinatedJointDisplay': 'Coordinated - Harmonized',
                    'costEstimatesUsd': 0,
                    'createdAt': '2021-01-01T00:00:00.123456+00:00',
                    'dataCollectionEndDate': '2020-09-06',
                    'dataCollectionStartDate': '2020-02-16',
                    'dataCollectionTechniques': '''Current hear claim well two truth out major. Upon these story film. Drive note bad rule.
She campaign little near enter their institution. Up sense ready require human.''',
                    'detailsType': 'MONITORING',
                    'detailsTypeDisplay': 'Monitoring',
                    'externalSupport': 'NO_EXTERNAL_SUPPORT_RECEIVED',
                    'externalSupportDisplay': 'No external support received',
                    'family': 'HUMANITARIAN_NEEDS_OVERVIEW',
                    'familyDisplay': 'Humanitarian Needs Overview (HNO)',
                    'focusComplete': True,
                    'focuses': [
                        'CONTEXT',
                        'HUMANITERIAN_ACCESS',
                        'DISPLACEMENT'
                    ],
                    'frequency': 'REGULAR',
                    'frequencyDisplay': 'Regular',
                    'id': '1',
                    'language': [
                        'ENGLISH',
                        'FRENCH'
                    ],
                    'lead': {
                        'id': '2'
                    },
                    'limitations': '''Choice father why often my security arm. Live try most arm meet surface attention attack. Identify walk now often always.
Price north first end prove fire. How public feel first sell.''',
                    'metadataComplete': True,
                    'methodologyAttributes': [
                    ],
                    'methodologyComplete': True,
                    'modifiedAt': '2021-01-01T00:00:00.123456+00:00',
                    'noOfPages': 0,
                    'objectives': '''Then fire pretty how trip learn enter. Seat much section investment on.
Young catch management sense technology. Physical society instead as. Other life edge network wall quite.''',
                    'protectionInfoMgmts': [
                        'PROTECTION_MONITORING'
                    ],
                    'protectionRisks': [
                    ],
                    'publicationDate': '2021-06-21',
                    'sampling': '''Best issue interest level. Pull worker better.
Song body court movie cell contain. Economic type kitchen technology nearly anything yourself. Why unit support.''',
                    'sectors': [
                        'HEALTH',
                        'SHELTER',
                        'WASH'
                    ],
                    'status': 'ONGOING',
                    'summaryComplete': True,
                    'summaryDimensionMeta': [
                    ],
                    'summaryPillarMeta': None,
                    'summarySubDimensionIssue': [
                    ],
                    'summarySubPillarIssue': [
                    ]
                }
            }
        }
    }
}
