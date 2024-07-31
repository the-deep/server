# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot


snapshots = Snapshot()

snapshots['TestGenericExportMutationSchema::test_project_stats generic-export-csv'] = '''ID,Title,Created Date,Owners,Start Date,End Date,Last Entry (Date),Organisation (Project owner),Project Stakeholders,Geo Areas,Analysis Framework,Description,Status,Test project (Y/N),Members Count,Sources Count,Entries Count,# of Exports\r
2,Project-1,2021-01-01 00:00:00.123456+00:00,,,,,,,,AF-0,,inactive,N,0,0,0,0\r
1,Project-0,2021-01-01 00:00:00.123456+00:00,,,,2021-01-01 00:00:00.123456+00:00,,,,AF-0,,inactive,N,0,1,20,0\r
'''
