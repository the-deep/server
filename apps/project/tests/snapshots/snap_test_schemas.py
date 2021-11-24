# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot


snapshots = Snapshot()

snapshots['TestProjectExploreStats::test_snapshot no-data'] = {
    'data': {
        'projectExploreStats': {
            'calculatedAt': '2021-01-01T00:00:00.123456+00:00',
            'dailyAverageLeadsTaggedPerProject': 0.0,
            'totalProjects': 0,
            'totalUsers': 1,
            'generatedExportsMonthly': 0,
            'leadsAddedWeekly': 0,
            'topActiveProjects': [
            ]
        }
    }
}

snapshots['TestProjectExploreStats::test_snapshot only-project'] = {
    'data': {
        'projectExploreStats': {
            'calculatedAt': '2021-01-01T00:00:00.123456+00:00',
            'totalProjects': 7,
            'totalUsers': 1,
            'dailyAverageLeadsTaggedPerProject': 0.0,
            'generatedExportsMonthly': 0,
            'leadsAddedWeekly': 0,
            'topActiveProjects': [
                {
                    'analysisFrameworkId': None,
                    'analysisFrameworkTitle': None,
                    'projectId': '1',
                    'projectTitle': 'Project-0'
                },
                {
                    'analysisFrameworkId': None,
                    'analysisFrameworkTitle': None,
                    'projectId': '2',
                    'projectTitle': 'Project-1'
                },
                {
                    'analysisFrameworkId': None,
                    'analysisFrameworkTitle': None,
                    'projectId': '3',
                    'projectTitle': 'Project-2'
                },
                {
                    'analysisFrameworkId': '1',
                    'analysisFrameworkTitle': 'AF-0',
                    'projectId': '4',
                    'projectTitle': 'Project-3'
                },
                {
                    'analysisFrameworkId': '1',
                    'analysisFrameworkTitle': 'AF-0',
                    'projectId': '5',
                    'projectTitle': 'Project-4'
                }
            ]
        }
    }
}

snapshots['TestProjectExploreStats::test_snapshot with-data'] = {
    'data': {
        'projectExploreStats': {
            'calculatedAt': '2021-01-01T00:00:00.123456+00:00',
            'totalProjects': 7,
            'totalUsers': 1,
            'dailyAverageLeadsTaggedPerProject': 0.10204081632653061,
            'generatedExportsMonthly': 3,
            'leadsAddedWeekly': 6,
            'topActiveProjects': [
                {
                    'analysisFrameworkId': '1',
                    'analysisFrameworkTitle': 'AF-0',
                    'projectId': '5',
                    'projectTitle': 'Project-4'
                },
                {
                    'analysisFrameworkId': '1',
                    'analysisFrameworkTitle': 'AF-0',
                    'projectId': '4',
                    'projectTitle': 'Project-3'
                },
                {
                    'analysisFrameworkId': None,
                    'analysisFrameworkTitle': None,
                    'projectId': '1',
                    'projectTitle': 'Project-0'
                },
                {
                    'analysisFrameworkId': None,
                    'analysisFrameworkTitle': None,
                    'projectId': '2',
                    'projectTitle': 'Project-1'
                },
                {
                    'analysisFrameworkId': None,
                    'analysisFrameworkTitle': None,
                    'projectId': '3',
                    'projectTitle': 'Project-2'
                }
            ]
        }
    }
}
