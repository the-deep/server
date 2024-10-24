import datetime

from unittest.mock import patch

from utils.graphene.tests import GraphQLTestCase, GraphQLSnapShotTestCase

from user.factories import UserFactory
from project.factories import ProjectFactory
from export.factories import ExportFactory
from analysis.factories import AnalysisFactory
from analysis_framework.factories import AnalysisFrameworkFactory
from lead.factories import LeadFactory
from entry.factories import EntryFactory

from lead.models import Lead
from export.models import Export, GenericExport, export_upload_to
from export.tasks import get_export_filename
from export.serializers import UserExportCreateGqlSerializer

from entry.models import Entry


class TestExportMutationSchema(GraphQLTestCase):
    CREATE_EXPORT_QUERY = '''
        mutation MyMutation ($projectId: ID!, $input: ExportCreateInputType!) {
          project(id: $projectId) {
            exportCreate(data: $input) {
              ok
              errors
              result {
                id
                title
                type
                status
                mimeType
                isPreview
                isArchived
                format
                filters {
                    assignees
                    authorOrganizations
                    authoringOrganizationTypes
                    confidentiality
                    createdAt
                    createdAtGte
                    createdAtLte
                    createdBy
                    emmEntities
                    emmKeywords
                    emmRiskFactors
                    entriesFilterData {
                      controlled
                      createdAt
                      createdAtGte
                      createdAtLte
                      createdBy
                      entriesId
                      entryTypes
                      excerpt
                      filterableData {
                        filterKey
                        includeSubRegions
                        useAndOperator
                        useExclude
                        value
                        valueGte
                        valueList
                        valueLte
                      }
                      geoCustomShape
                      id
                      leadAssignees
                      leadAuthorOrganizations
                      leadAuthoringOrganizationTypes
                      leadConfidentialities
                      leadCreatedBy
                      leadGroupLabel
                      leadPriorities
                      leadPublishedOn
                      leadPublishedOnGte
                      leadPublishedOnLte
                      leadSourceOrganizations
                      leadStatuses
                      leadTitle
                      leads
                      search
                      projectEntryLabels
                      modifiedBy
                      modifiedAtLte
                      modifiedAtGte
                      modifiedAt
                    }
                    url
                    text
                    statuses
                    sourceTypes
                    sourceOrganizations
                    search
                    publishedOnLte
                    publishedOnGte
                    publishedOn
                    priorities
                    ordering
                    modifiedBy
                    modifiedAtLte
                    modifiedAtGte
                    modifiedAt
                    ids
                    hasEntries
                    hasAssessment
                    extractionStatus
                    excludeProvidedLeadsId
                }
                file {
                  name
                  url
                }
                exportedAt
                exportType
                project
                exportedBy {
                  id
                  displayName
                }
                analysis {
                    id
                    title
                }
              }
            }
          }
        }
    '''

    UPDATE_EXPORT_QUERY = '''
        mutation MyMutation ($projectId: ID!, $exportId: ID!, $input: ExportUpdateInputType!) {
          project(id: $projectId) {
            exportUpdate(id: $exportId, data: $input) {
              ok
              errors
              result {
                id
                title
                type
                status
                mimeType
                isPreview
                isArchived
                format
                filters {
                    assignees
                    authorOrganizations
                    authoringOrganizationTypes
                    confidentiality
                    createdAt
                    createdAtGte
                    createdAtLte
                    createdBy
                    emmEntities
                    emmKeywords
                    emmRiskFactors
                    entriesFilterData {
                      controlled
                      createdAt
                      createdAtGte
                      createdAtLte
                      createdBy
                      entriesId
                      entryTypes
                      excerpt
                      filterableData {
                        filterKey
                        includeSubRegions
                        useAndOperator
                        useExclude
                        value
                        valueGte
                        valueList
                        valueLte
                      }
                      geoCustomShape
                      id
                      leadAssignees
                      leadAuthorOrganizations
                      leadAuthoringOrganizationTypes
                      leadConfidentialities
                      leadCreatedBy
                      leadGroupLabel
                      leadPriorities
                      leadPublishedOn
                      leadPublishedOnGte
                      leadPublishedOnLte
                      leadSourceOrganizations
                      leadStatuses
                      leadTitle
                      leads
                      search
                      projectEntryLabels
                      modifiedBy
                      modifiedAtLte
                      modifiedAtGte
                      modifiedAt
                    }
                    url
                    text
                    statuses
                    sourceTypes
                    sourceOrganizations
                    search
                    publishedOnLte
                    publishedOnGte
                    publishedOn
                    priorities
                    ordering
                    modifiedBy
                    modifiedAtLte
                    modifiedAtGte
                    modifiedAt
                    ids
                    hasEntries
                    hasAssessment
                    extractionStatus
                    excludeProvidedLeadsId
                }
                file {
                  name
                  url
                }
                exportedAt
                exportType
                project
                exportedBy {
                  id
                  displayName
                }
                analysis {
                    id
                    title
                }
              }
            }
          }
        }
    '''

    CANCEL_EXPORT_QUERY = '''
        mutation MyMutation ($projectId: ID!, $exportId: ID!) {
          project(id: $projectId) {
            exportCancel(id: $exportId) {
              ok
              errors
              result {
                id
                title
                type
                status
                mimeType
                isPreview
                isArchived
                format
                filters {
                    assignees
                    authorOrganizations
                    authoringOrganizationTypes
                    confidentiality
                    createdAt
                    createdAtGte
                    createdAtLte
                    createdBy
                    emmEntities
                    emmKeywords
                    emmRiskFactors
                    entriesFilterData {
                      controlled
                      createdAt
                      createdAtGte
                      createdAtLte
                      createdBy
                      entriesId
                      entryTypes
                      excerpt
                      filterableData {
                        filterKey
                        includeSubRegions
                        useAndOperator
                        useExclude
                        value
                        valueGte
                        valueList
                        valueLte
                      }
                      geoCustomShape
                      id
                      leadAssignees
                      leadAuthorOrganizations
                      leadAuthoringOrganizationTypes
                      leadConfidentialities
                      leadCreatedBy
                      leadGroupLabel
                      leadPriorities
                      leadPublishedOn
                      leadPublishedOnGte
                      leadPublishedOnLte
                      leadSourceOrganizations
                      leadStatuses
                      leadTitle
                      leads
                      search
                      projectEntryLabels
                      modifiedBy
                      modifiedAtLte
                      modifiedAtGte
                      modifiedAt
                    }
                    url
                    text
                    statuses
                    sourceTypes
                    sourceOrganizations
                    search
                    publishedOnLte
                    publishedOnGte
                    publishedOn
                    priorities
                    ordering
                    modifiedBy
                    modifiedAtLte
                    modifiedAtGte
                    modifiedAt
                    ids
                    hasEntries
                    hasAssessment
                    extractionStatus
                    excludeProvidedLeadsId
                }
                file {
                  name
                  url
                }
                exportedAt
                exportType
                project
                exportedBy {
                  id
                  displayName
                }
              }
            }
          }
        }
    '''

    DELETE_EXPORT_QUERY = '''
        mutation MyMutation ($projectId: ID!, $exportId: ID!) {
          project(id: $projectId) {
            exportDelete(id: $exportId) {
              ok
              errors
              result {
                id
                title
                type
                status
                mimeType
                isPreview
                isArchived
                format
                filters {
                    assignees
                    authorOrganizations
                    authoringOrganizationTypes
                    confidentiality
                    createdAt
                    createdAtGte
                    createdAtLte
                    createdBy
                    emmEntities
                    emmKeywords
                    emmRiskFactors
                    entriesFilterData {
                      controlled
                      createdAt
                      createdAtGte
                      createdAtLte
                      createdBy
                      entriesId
                      entryTypes
                      excerpt
                      filterableData {
                        filterKey
                        includeSubRegions
                        useAndOperator
                        useExclude
                        value
                        valueGte
                        valueList
                        valueLte
                      }
                      geoCustomShape
                      id
                      leadAssignees
                      leadAuthorOrganizations
                      leadAuthoringOrganizationTypes
                      leadConfidentialities
                      leadCreatedBy
                      leadGroupLabel
                      leadPriorities
                      leadPublishedOn
                      leadPublishedOnGte
                      leadPublishedOnLte
                      leadSourceOrganizations
                      leadStatuses
                      leadTitle
                      leads
                      search
                      projectEntryLabels
                      modifiedBy
                      modifiedAtLte
                      modifiedAtGte
                      modifiedAt
                    }
                    url
                    text
                    statuses
                    sourceTypes
                    sourceOrganizations
                    search
                    publishedOnLte
                    publishedOnGte
                    publishedOn
                    priorities
                    ordering
                    modifiedBy
                    modifiedAtLte
                    modifiedAtGte
                    modifiedAt
                    ids
                    hasEntries
                    hasAssessment
                    extractionStatus
                    excludeProvidedLeadsId
                }
                file {
                  name
                  url
                }
                exportedAt
                exportType
                project
                exportedBy {
                  id
                  displayName
                }
              }
            }
          }
        }
    '''

    def setUp(self):
        super().setUp()
        self.project = ProjectFactory.create()
        # User with role
        self.non_member_user = UserFactory.create()
        self.readonly_member_user = UserFactory.create()
        self.member_user = UserFactory.create()
        self.another_member_user = UserFactory.create()
        self.project.add_member(self.readonly_member_user, role=self.project_role_reader_non_confidential)
        self.project.add_member(self.member_user, role=self.project_role_member)
        self.project.add_member(self.another_member_user, role=self.project_role_member)
        self.common_export_attrs = dict(
            project=self.project,
            format=Export.Format.DOCX,
            type=Export.DataType.ENTRIES,
            export_type=Export.ExportType.REPORT,
        )

    def test_export_create(self):
        """
        This test makes sure only valid users can create export
        """
        def _query_check(minput, **kwargs):
            return self.query_check(
                self.CREATE_EXPORT_QUERY,
                minput=minput,
                variables={'projectId': self.project.id},
                **kwargs
            )

        minput = dict(
            format=self.genum(Export.Format.PDF),
            type=self.genum(Export.DataType.ENTRIES),
            title='Export 101',
            exportType=self.genum(Export.ExportType.EXCEL),
            isPreview=False,

            filters={
                'ids': [],
                'search': None,
                'statuses': [
                    self.genum(Lead.Status.NOT_TAGGED),
                    self.genum(Lead.Status.IN_PROGRESS),
                    self.genum(Lead.Status.TAGGED),
                ],
                'assignees': None,
                'priorities': None,
                'createdAtGte': '2021-11-01T00:00:00Z',
                'createdAtLte': '2021-01-01T00:00:00Z',
                'confidentiality': None,
                'publishedOnGte': None,
                'publishedOnLte': None,
                'excludeProvidedLeadsId': True,
                'authoringOrganizationTypes': None,
                'hasEntries': True,
                'entriesFilterData': {
                    'controlled': None,
                    'createdBy': None,
                    'entryTypes': None,
                    'filterableData': [
                        {
                            'filterKey': 'random-element-1',
                            'value': None,
                            'valueGte': None,
                            'valueLte': None,
                            'valueList': [
                                'random-value-1',
                                'random-value-2',
                                'random-value-3',
                                'random-value-4',
                            ],
                            'useExclude': None,
                            'useAndOperator': None,
                            'includeSubRegions': None,
                        }
                    ]
                },
            },
        )
        # -- Without login
        _query_check(minput, assert_for_error=True)

        # -- With login (non-member)
        self.force_login(self.non_member_user)
        _query_check(minput, assert_for_error=True)

        # --- member user
        self.force_login(self.member_user)
        # ----- (Simple validation)
        response = _query_check(minput, okay=False)['data']
        self.assertEqual(response['project']['exportCreate']['result'], None, response)

        # -----
        minput['format'] = self.genum(Export.Format.XLSX)
        response = _query_check(minput)['data']
        response_export = response['project']['exportCreate']['result']
        self.assertNotEqual(response_export, None, response)
        export = Export.objects.get(pk=response_export['id'])
        excepted_filters = {
            'ids': [],
            'search': None,
            'statuses': [
                'pending',
                'processed',
                'validated',
            ],
            'assignees': None,
            'priorities': None,
            'created_at_gte': '2021-11-01T00:00:00Z',
            'created_at_lte': '2021-01-01T00:00:00Z',
            'confidentiality': None,
            'published_on_gte': None,
            'published_on_lte': None,
            'exclude_provided_leads_id': True,
            'authoring_organization_types': None,
            'has_entries': True,
            'entries_filter_data': {
                'controlled': None,
                'created_by': None,
                'entry_types': None,
                'filterable_data': [
                    {
                        'value': None,
                        'value_gte': None,
                        'value_lte': None,
                        'filter_key': 'random-element-1',
                        'value_list': [
                            'random-value-1',
                            'random-value-2',
                            'random-value-3',
                            'random-value-4'
                        ],
                        'use_exclude': None,
                        'use_and_operator': None,
                        'include_sub_regions': None
                    }
                ]
            },
        }
        # Make sure the filters are stored in db properly
        self.assertEqual(export.filters, excepted_filters, response)

    def test_export_update(self):
        """
        This test makes sure only valid users can update export
        """
        export = ExportFactory.create(exported_by=self.member_user, **self.common_export_attrs)
        export_2 = ExportFactory.create(
            title='Export 2',
            exported_by=self.member_user,
            **self.common_export_attrs,
        )

        def _query_check(minput, **kwargs):
            return self.query_check(
                self.UPDATE_EXPORT_QUERY,
                minput=minput,
                mnested=['project'],
                variables={
                    'projectId': self.project.id,
                    'exportId': export.id,
                },
                **kwargs
            )

        # Snapshot
        export_data = UserExportCreateGqlSerializer(instance=export).data

        minput = dict(title=export_2.title)
        # -- Without login
        _query_check(minput, assert_for_error=True)

        # -- With login (non-member)
        self.force_login(self.non_member_user)
        _query_check(minput, assert_for_error=True)

        # --- member user
        self.force_login(self.member_user)
        # -----
        minput['title'] = 'Export 1 (Updated)'
        response = _query_check(minput, okay=True)['data']
        response_export = response['project']['exportUpdate']['result']
        self.assertNotEqual(response_export, None, response)
        export.refresh_from_db()
        updated_export_data = UserExportCreateGqlSerializer(export).data
        # Make sure the filters are stored in db properly
        self.assertNotEqual(updated_export_data, export_data, response)
        export_data['title'] = minput['title']
        self.assertEqual(updated_export_data, export_data, response)

    def test_analysis_export(self):
        # create analysis
        analysis1 = AnalysisFactory.create(
            project=self.project,
            end_date=datetime.datetime.now(),
            team_lead=self.member_user
        )

        def _query_check(minput, **kwargs):
            return self.query_check(
                self.CREATE_EXPORT_QUERY,
                minput=minput,
                variables={'projectId': self.project.id},
                **kwargs
            )

        minput = dict(
            format=self.genum(Export.Format.XLSX),
            type=self.genum(Export.DataType.ANALYSES),
            title='Analysis Export 100',
            exportType=self.genum(Export.ExportType.EXCEL),
            analysis=analysis1.id,
            filters={},
        )
        # -- Without login
        _query_check(minput, assert_for_error=True)

        # -- With login (non-member)
        self.force_login(self.non_member_user)
        _query_check(minput, assert_for_error=True)

        # --- member user
        self.force_login(self.member_user)

        response = _query_check(minput, okay=False)['data']
        self.assertNotEqual(response['project']['exportCreate']['result'], None, response)
        self.assertEqual(response['project']['exportCreate']['result']['analysis']['title'], analysis1.title)

        # TODO: Add test case for file check

    def test_export_cancel(self):
        """
        This test makes sure only valid users can cancel export
        """
        def _query_check(export, **kwargs):
            return self.query_check(
                self.CANCEL_EXPORT_QUERY,
                variables={'projectId': self.project.id, 'exportId': export.id},
                **kwargs
            )

        export_pending = ExportFactory.create(
            exported_by=self.member_user, status=Export.Status.PENDING, **self.common_export_attrs)
        export_failed = ExportFactory.create(
            exported_by=self.member_user, status=Export.Status.FAILURE, **self.common_export_attrs)
        export2 = ExportFactory.create(exported_by=self.another_member_user, **self.common_export_attrs)

        # -- Without login
        _query_check(export_pending, assert_for_error=True)

        # -- With login (non-member)
        self.force_login(self.non_member_user)
        _query_check(export_pending, assert_for_error=True)

        # --- member user (read-only)
        self.force_login(self.readonly_member_user)
        _query_check(export_pending, okay=False)

        # --- member user (but not owner)
        self.force_login(self.member_user)
        _query_check(export2, okay=False)

        # --- member user (with ownership)
        self.force_login(self.member_user)
        content = _query_check(export_failed)['data']['project']['exportCancel']['result']
        self.assertEqual(content['status'], self.genum(Export.Status.FAILURE), content)

        content = _query_check(export_pending)['data']['project']['exportCancel']['result']
        self.assertEqual(content['status'], self.genum(Export.Status.CANCELED), content)

    def test_export_delete(self):
        """
        This test makes sure only valid users can delete export
        """
        def _query_check(export, **kwargs):
            return self.query_check(
                self.DELETE_EXPORT_QUERY,
                variables={'projectId': self.project.id, 'exportId': export.id},
                **kwargs
            )

        export1 = ExportFactory.create(exported_by=self.member_user, **self.common_export_attrs)
        export2 = ExportFactory.create(exported_by=self.another_member_user, **self.common_export_attrs)

        # -- Without login
        _query_check(export1, assert_for_error=True)

        # -- With login (non-member)
        self.force_login(self.non_member_user)
        _query_check(export1, assert_for_error=True)

        # --- member user (read-only)
        self.force_login(self.readonly_member_user)
        _query_check(export1, okay=False)

        # --- member user (but not owner)
        self.force_login(self.member_user)
        _query_check(export2, okay=False)

        # --- member user (with ownership)
        self.force_login(self.member_user)
        content = _query_check(export1)['data']['project']['exportDelete']['result']
        self.assertEqual(content['id'], str(export1.id), content)


class TestGenericExportMutationSchema(GraphQLSnapShotTestCase):
    factories_used = [AnalysisFrameworkFactory, ProjectFactory, LeadFactory, UserFactory]
    ENABLE_NOW_PATCHER = True

    CREATE_GENERIC_EXPORT_QUERY = '''
        mutation MyMutation ($input: GenericExportCreateInputType!) {
            genericExportCreate(data: $input) {
              ok
              errors
              result {
                id
                title
                type
                status
                mimeType
                format
                filters
                file {
                  name
                  url
                }
                exportedAt
                exportedBy {
                  id
                  displayName
                }
              }
            }
        }
    '''

    def setUp(self):
        super().setUp()
        # TODO: Add more fixture here.
        self.af = AnalysisFrameworkFactory.create()
        self.project, *_ = ProjectFactory.create_batch(2, analysis_framework=self.af)
        self.lead = LeadFactory.create(project=self.project)
        EntryFactory.create_batch(10, lead=self.lead, project=self.project, analysis_framework=self.af)
        EntryFactory.create_batch(
            10,
            lead=self.lead,
            project=self.project,
            analysis_framework=self.af,
            entry_type=Entry.TagType.ATTACHMENT
        )
        # User with role
        self.user = UserFactory.create()
        # -- Some other data which shouldn't be visible in exports
        # Private project
        ProjectFactory.create(analysis_framework=self.af, is_private=True)
        # Project created around the filter
        self.update_obj(
            ProjectFactory.create(analysis_framework=self.af),
            created_at=self.PATCHER_NOW_VALUE - datetime.timedelta(days=11),
        )
        self.update_obj(
            ProjectFactory.create(analysis_framework=self.af),
            created_at=self.PATCHER_NOW_VALUE + datetime.timedelta(days=11),
        )

    def test_project_stats(self):
        def _query_check(minput, **kwargs):
            return self.query_check(
                self.CREATE_GENERIC_EXPORT_QUERY,
                minput=minput,
                **kwargs
            )

        minput = dict(
            format=self.genum(GenericExport.Format.CSV),
            type=self.genum(GenericExport.DataType.PROJECTS_STATS),
            filters={
                "deepExplore": {
                    "dateFrom": self.get_datetime_str(self.PATCHER_NOW_VALUE - datetime.timedelta(days=10)),
                    "dateTo": self.get_datetime_str(self.PATCHER_NOW_VALUE + datetime.timedelta(days=10)),
                }
            },
        )
        # -- Without login
        _query_check(minput, assert_for_error=True)

        # --- with login
        self.force_login(self.user)

        with self.captureOnCommitCallbacks(execute=True):
            response = _query_check(minput, okay=True)['data']
        self.assertNotEqual(response['genericExportCreate']['result'], None, response)
        generic_export = GenericExport.objects.get(pk=response['genericExportCreate']['result']['id'])
        self.assertEqual(generic_export.status, GenericExport.Status.SUCCESS, response)
        self.assertNotEqual(generic_export.file.name, None, response)
        self.assertMatchSnapshot(generic_export.file.read().decode('utf-8'), 'generic-export-csv')


class GeneraltestCase(GraphQLTestCase):
    def test_export_path_generation(self):
        MOCK_TIME_STR = '20211205'
        MOCK_RANDOM_STRING = 'random-string'
        user = UserFactory.create()
        project = ProjectFactory.create()
        common_args = {
            'type': Export.DataType.ENTRIES,
            'exported_by': user,
            'project': project,
        }
        with \
                patch('export.models.get_random_string') as get_random_string_mock, \
                patch('export.models.timezone') as timezone_mock:
            get_random_string_mock.return_value = MOCK_RANDOM_STRING
            timezone_mock.now.return_value.strftime.return_value = MOCK_TIME_STR
            for export, expected_title, expected_filename, _type in [
                (
                    ExportFactory(
                        title='',
                        format=Export.Format.DOCX,
                        export_type=Export.ExportType.REPORT,
                        **common_args
                    ),
                    f'{MOCK_TIME_STR} DEEP Entries General Export',
                    f'{MOCK_TIME_STR} DEEP Entries General Export.docx',
                    'without-title',
                ),
                (
                    ExportFactory(
                        title='test 123',
                        format=Export.Format.PDF,
                        export_type=Export.ExportType.REPORT,
                        **common_args,
                    ),
                    'test 123',
                    'test 123.pdf',
                    'with-title-01',
                ),
                (
                    ExportFactory(
                        title='test 321',
                        format=Export.Format.JSON,
                        export_type=Export.ExportType.JSON,
                        is_preview=True,
                        **common_args,
                    ),
                    'test 321',
                    '(Preview) test 321.json',
                    'with-title-02',
                ),
            ]:
                export.save()
                # generated_title = Export.generate_title(export.type, export.format)
                # export.title = export.title or generated_title  # This is automatically done on export save (mocking here)
                generated_filename = export_upload_to(export, get_export_filename(export))
                self.assertEqual(export.title, expected_title, _type)
                self.assertEqual(generated_filename, f'export/{MOCK_RANDOM_STRING}/{expected_filename}', _type)
