import copy
import json
from unittest import mock

from django.core.files.temp import NamedTemporaryFile
from utils.graphene.tests import GraphQLTestCase, GraphQLSnapShotTestCase
from user.factories import UserFactory
from graphene_file_upload.django.testing import GraphQLFileUploadTestCase

from analysis_framework.models import Widget

from project.models import ProjectChangeLog
from project.factories import ProjectFactory
from organization.factories import OrganizationFactory
from analysis_framework.models import AnalysisFramework
from analysis_framework.factories import (
    AnalysisFrameworkFactory,
    SectionFactory,
    WidgetFactory,
)


class TestPreviewImage(GraphQLFileUploadTestCase, GraphQLTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.user = UserFactory.create()
        self.upload_mutation = """
            mutation Mutation($data: AnalysisFrameworkInputType!) {
              analysisFrameworkCreate(data: $data) {
                ok
                errors
                result {
                  id
                  title
                  previewImage {
                      name
                      url
                  }
                }
              }
            }
        """
        self.retrieve_af_query = """
        query RetrieveAFQuery {
          analysisFramework(id: %s) {
            id
            previewImage {
                name
                url
            }
          }
        }
        """
        self.variables = {
            "data": {"title": 'test', "previewImage": None}
        }
        self.force_login(self.user)

    def test_upload_preview_image(self):
        file_text = b'preview image text'
        with NamedTemporaryFile(suffix='.png') as t_file:
            t_file.write(file_text)
            t_file.seek(0)
            response = self._client.post(
                '/graphql',
                data={
                    'operations': json.dumps({
                        'query': self.upload_mutation,
                        'variables': self.variables
                    }),
                    't_file': t_file,
                    'map': json.dumps({
                        't_file': ['variables.data.previewImage']
                    })
                }
            )
        content = response.json()
        self.assertResponseNoErrors(response)

        # Test can upload image
        af_id = content['data']['analysisFrameworkCreate']['result']['id']
        self.assertTrue(content['data']['analysisFrameworkCreate']['ok'], content)
        self.assertTrue(content['data']['analysisFrameworkCreate']['result']['previewImage']["name"])
        preview_image_name = content['data']['analysisFrameworkCreate']['result']['previewImage']["name"]
        preview_image_url = content['data']['analysisFrameworkCreate']['result']['previewImage']["url"]
        self.assertTrue(preview_image_name.endswith('.png'))
        self.assertTrue(preview_image_url.endswith(preview_image_name))

        # Test can retrive image
        response = self.query(self.retrieve_af_query % af_id)
        self.assertResponseNoErrors(response)
        content = response.json()
        self.assertTrue(content['data']['analysisFramework']['previewImage']["name"])
        preview_image_name = content['data']['analysisFramework']['previewImage']["name"]
        preview_image_url = content['data']['analysisFramework']['previewImage']["url"]
        self.assertTrue(preview_image_name.endswith('.png'))
        self.assertTrue(preview_image_url.endswith(preview_image_name))


class TestAnalysisFrameworkMutationSnapShotTestCase(GraphQLSnapShotTestCase):
    factories_used = [AnalysisFrameworkFactory, SectionFactory, WidgetFactory]

    def setUp(self):
        super().setUp()
        self.create_query = '''
            mutation MyMutation ($input: AnalysisFrameworkInputType!) {
              __typename
              analysisFrameworkCreate(data: $input) {
                ok
                errors
                result {
                  id
                  isPrivate
                  description
                  currentUserRole
                  title
                  primaryTagging {
                    id
                    order
                    title
                    tooltip
                    clientId
                    widgets {
                      id
                      key
                      order
                      properties
                      title
                      widgetId
                      version
                      clientId
                    }
                  }
                  secondaryTagging {
                    id
                    key
                    order
                    properties
                    title
                    widgetId
                    version
                    clientId
                  }
                }
              }
            }
        '''

        self.organization1 = OrganizationFactory.create()
        self.invalid_minput = dict(
            title='',
            description='Af description',
            isPrivate=False,
            organization=str(self.organization1.id),
            # previewImage='',
            primaryTagging=[
                dict(
                    title='',
                    clientId='section-101',
                    order=2,
                    tooltip='Tooltip for section 101',
                    widgets=[
                        dict(
                            clientId='section-text-101-client-id',
                            title='',
                            widgetId=self.genum(Widget.WidgetType.TEXT),
                            version=1,
                            key='section-text-101',
                            order=1,
                            properties=dict(),
                        ),
                        dict(
                            clientId='section-text-102-client-id',
                            title='',
                            widgetId=self.genum(Widget.WidgetType.TEXT),
                            version=1,
                            key='section-text-102',
                            order=2,
                            properties=dict(),
                        ),
                    ],
                ),
                dict(
                    title='',
                    clientId='section-102',
                    order=1,
                    tooltip='Tooltip for section 102',
                    widgets=[
                        dict(
                            clientId='section-2-text-101-client-id',
                            title='Section-2-Text-101',
                            widgetId=self.genum(Widget.WidgetType.TEXT),
                            version=1,
                            key='section-2-text-101',
                            order=1,
                            properties=dict(),
                        ),
                        dict(
                            clientId='section-2-text-102-client-id',
                            title='Section-2-Text-102',
                            widgetId=self.genum(Widget.WidgetType.TEXT),
                            version=1,
                            key='section-2-text-102',
                            order=2,
                            properties=dict(),
                        ),
                    ],
                ),
            ],
            secondaryTagging=[
                dict(
                    clientId='select-widget-101-client-id',
                    title='',
                    widgetId=self.genum(Widget.WidgetType.SELECT),
                    version=1,
                    key='select-widget-101-key',
                    order=1,
                    properties=dict(),
                ),
                dict(
                    clientId='multi-select-widget-102-client-id',
                    title='multi-select-Widget-2',
                    widgetId=self.genum(Widget.WidgetType.MULTISELECT),
                    version=1,
                    key='multi-select-widget-102-key',
                    order=2,
                    properties=dict(),
                ),
            ],
        )

        self.valid_minput = dict(
            title='AF (TEST)',
            description='Af description',
            isPrivate=False,
            organization=str(self.organization1.id),
            properties=dict(),
            # previewImage='',
            primaryTagging=[
                dict(
                    title='Section 101',
                    clientId='section-101',
                    order=2,
                    tooltip='Tooltip for section 101',
                    widgets=[
                        dict(
                            clientId='section-text-101-client-id',
                            title='Section-Text-101',
                            widgetId=self.genum(Widget.WidgetType.MATRIX1D),
                            version=1,
                            key='section-text-101',
                            order=1,
                            properties=dict(
                                rows=[
                                    dict(
                                        key='row-key-1',
                                        label='Row Label 1',
                                        cells=[
                                            dict(key='cell-key-1.1', label='Cell Label 1.1'),
                                            dict(key='cell-key-1.2', label='Cell Label 1.2'),
                                            dict(key='cell-key-1.3', label='Cell Label 1.3'),
                                        ],
                                    ),
                                    dict(
                                        key='row-key-2',
                                        label='Row Label 2',
                                        cells=[
                                            dict(key='cell-key-2.1', label='Cell Label 2.1'),
                                            dict(key='cell-key-2.2', label='Cell Label 2.2'),
                                        ],
                                    ),

                                ],
                            ),
                        ),
                        dict(
                            clientId='section-text-102-client-id',
                            title='Section-Text-102',
                            widgetId=self.genum(Widget.WidgetType.MATRIX2D),
                            version=1,
                            key='section-text-102',
                            order=2,
                            properties=dict(
                                rows=[
                                    dict(
                                        key='row-key-1',
                                        label='Row Label 1',
                                        subRows=[
                                            dict(key='sub-row-key-1.1', label='SubRow Label 1.1'),
                                            dict(key='sub-row-key-1.2', label='SubRow Label 1.2'),
                                            dict(key='sub-row-key-1.3', label='SubRow Label 1.3'),
                                        ],
                                    ),
                                    dict(
                                        key='row-key-2',
                                        label='Row Label 2',
                                        subRows=[
                                            dict(key='sub-row-key-2.1', label='SubRow Label 2.1'),
                                            dict(key='sub-row-key-2.2', label='SubRow Label 2.2'),
                                        ],
                                    ),
                                ],
                                columns=[
                                    dict(
                                        key='column-key-1',
                                        label='Column Label 1',
                                        subColumns=[
                                            dict(key='sub-column-key-1.1', label='SubColumn Label 1.1'),
                                            dict(key='sub-column-key-1.2', label='SubColumn Label 1.2'),
                                            dict(key='sub-column-key-1.3', label='SubColumn Label 1.3'),
                                        ],
                                    ),
                                    dict(
                                        key='column-key-2',
                                        label='Column Label 2',
                                        subColumns=[
                                            dict(key='sub-column-key-2.1', label='SubColumn Label 2.1'),
                                            dict(key='sub-column-key-2.2', label='SubColumn Label 2.2'),
                                        ],
                                    ),
                                    dict(
                                        key='column-key-3',
                                        label='Column Label 3',
                                        subColumns=[],
                                    ),
                                ],
                            ),
                        ),
                    ],
                ),
                dict(
                    title='Section 102',
                    clientId='section-102',
                    order=1,
                    tooltip='Tooltip for section 102',
                    widgets=[
                        dict(
                            clientId='section-2-text-101-client-id',
                            title='Section-2-Text-101',
                            widgetId=self.genum(Widget.WidgetType.TEXT),
                            version=1,
                            key='section-2-text-101',
                            order=1,
                            properties=dict(),
                        ),
                        dict(
                            clientId='section-2-text-102-client-id',
                            title='Section-2-Text-102',
                            widgetId=self.genum(Widget.WidgetType.TEXT),
                            version=1,
                            key='section-2-text-102',
                            order=2,
                            properties=dict(),
                        ),
                    ],
                ),
            ],
            secondaryTagging=[
                dict(
                    clientId='select-widget-101-client-id',
                    title='Select-Widget-1',
                    widgetId=self.genum(Widget.WidgetType.SELECT),
                    version=1,
                    key='select-widget-101-key',
                    order=1,
                    properties=dict(),
                ),
                dict(
                    clientId='multi-select-widget-102-client-id',
                    title='multi-select-Widget-2',
                    widgetId=self.genum(Widget.WidgetType.MULTISELECT),
                    version=1,
                    key='multi-select-widget-102-key',
                    order=2,
                    properties=dict(),
                ),
            ],
        )

    def test_analysis_framework_create(self):
        user = UserFactory.create()

        def _query_check(minput, **kwargs):
            return self.query_check(self.create_query, minput=minput, **kwargs)

        # Without login
        _query_check(self.valid_minput, assert_for_error=True)

        # With login
        self.force_login(user)

        response = _query_check(self.invalid_minput, okay=False)
        self.assertMatchSnapshot(response, 'errors')

        with self.captureOnCommitCallbacks(execute=True):
            response = _query_check(self.valid_minput, okay=True)
        self.assertMatchSnapshot(response, 'success')
        # Export test
        new_af = AnalysisFramework.objects.get(pk=response['data']['analysisFrameworkCreate']['result']['id'])
        self.assertMatchSnapshot(new_af.export.file.read().decode('utf-8'), 'success-af-export')

    def test_analysis_framework_update(self):
        query = '''
            mutation MyMutation ($id: ID! $input: AnalysisFrameworkInputType!) {
              __typename
              analysisFramework (id: $id ) {
                  analysisFrameworkUpdate(data: $input) {
                    ok
                    errors
                    result {
                      id
                      isPrivate
                      description
                      currentUserRole
                      title
                      properties {
                        statsConfig {
                          geoWidget {
                            pk
                          }
                          reliabilityWidget {
                            pk
                          }
                          severityWidget {
                            pk
                          }
                          widget1d {
                            pk
                          }
                          widget2d {
                            pk
                          }
                        multiselectWidgets {
                            pk
                          }
                          organigramWidgets {
                            pk
                          }
                        }
                      }
                      primaryTagging {
                        id
                        order
                        title
                        tooltip
                        clientId
                        widgets {
                          id
                          key
                          order
                          properties
                          title
                          widgetId
                          version
                          clientId
                          conditional {
                            parentWidget
                            parentWidgetType
                            conditions
                          }
                        }
                      }
                      secondaryTagging {
                        id
                        key
                        order
                        properties
                        title
                        widgetId
                        version
                        clientId
                        conditional {
                          parentWidget
                          parentWidgetType
                          conditions
                        }
                      }
                    }
                  }
              }
            }
        '''

        user = UserFactory.create()
        project1, project2, project3 = ProjectFactory.create_batch(3)

        def _query_check(id, minput, **kwargs):
            return self.query_check(
                query,
                minput=minput,
                mnested=['analysisFramework'],
                variables={'id': id},
                **kwargs,
            )

        # ---------- Without login
        valid_minput = copy.deepcopy(self.valid_minput)
        new_widgets = [
            dict(
                clientId='geo-widget-103-client-id',
                title='Geo',
                widgetId=self.genum(Widget.WidgetType.GEO),
                version=1,
                key='geo-widget-103-key',
                order=3,
                properties=dict(),
            ),
            dict(
                clientId='scale-widget-104-client-id',
                title='Scale',
                widgetId=self.genum(Widget.WidgetType.SCALE),
                version=1,
                key='scale-widget-104-key',
                order=4,
                properties=dict(),
            ),
            dict(
                clientId='organigram-widget-104-client-id',
                title='Organigram',
                widgetId=self.genum(Widget.WidgetType.ORGANIGRAM),
                version=1,
                key='organigram-widget-104-key',
                order=5,
                properties=dict(),
            ),
        ]
        valid_minput['secondaryTagging'].extend(new_widgets)
        _query_check(0, valid_minput, assert_for_error=True)
        # ---------- With login
        self.force_login(user)
        # ---------- Let's create a new AF (Using create test data)
        new_af_response = self.query_check(
            self.create_query, minput=valid_minput)['data']['analysisFrameworkCreate']['result']
        self.assertMatchSnapshot(copy.deepcopy(new_af_response), 'created')

        new_af_id = new_af_response['id']
        for project in [project1, project2]:
            project.analysis_framework_id = new_af_id
            project.save(update_fields=('analysis_framework_id',))

        # ---------------- Remove invalid attributes
        new_af_response.pop('currentUserRole')
        new_af_response.pop('id')
        # ---------- Let's change some attributes (for validation errors)
        new_af_response['title'] = ''
        new_af_response['primaryTagging'][0]['title'] = ''
        # ----------------- Let's try to update
        # ---- Add stats_config as well.

        widget_qs = Widget.objects.filter(analysis_framework=new_af_id)

        def _get_widget_ID(_type):
            widget = widget_qs.filter(widget_id=_type).first()
            if widget:
                return dict(
                    pk=str(widget.id)
                )

        def _get_multiple_widget_ID(_type):
            return [
                dict(
                    pk=str(widget.id)
                )
                for widget in widget_qs.filter(widget_id=_type)
            ]

        new_af_response['properties'] = dict(
            statsConfig=dict(
                # Invalid IDS
                geoWidget=_get_widget_ID(Widget.WidgetType.MULTISELECT),
                severityWidget=_get_widget_ID(Widget.WidgetType.MULTISELECT),
                reliabilityWidget=dict(pk='10000001'),
                # widget1d=_get_multiple_widget_ID(Widget.WidgetType.MULTISELECT),
                widget1d=_get_multiple_widget_ID(Widget.WidgetType.MULTISELECT),
                widget2d=_get_multiple_widget_ID(Widget.WidgetType.MULTISELECT),
                multiselectWidgets=_get_multiple_widget_ID(Widget.WidgetType.ORGANIGRAM),
                organigramWidgets=_get_multiple_widget_ID(Widget.WidgetType.MULTISELECT),
            ),
        )
        response = _query_check(new_af_id, new_af_response, okay=False)
        self.assertMatchSnapshot(response, 'errors')
        # ---------- Let's change some attributes (for success change)
        new_af_response['title'] = 'Updated AF (TEST)'
        new_af_response['description'] = 'Updated Af description'
        new_af_response['primaryTagging'][0]['title'] = 'Updated Section 102'
        new_af_response['primaryTagging'][0]['widgets'][0].pop('id')  # Remove/Create a widget
        new_af_response['primaryTagging'][0]['widgets'][1]['title'] = 'Updated-Section-2-Text-101'  # Remove a widget
        new_af_response['primaryTagging'][1].pop('id')  # Remove/Create second ordered section (but use current widgets)
        new_af_response['secondaryTagging'].pop(0)  # Remove another widget
        new_af_response['secondaryTagging'][0].pop('id')  # Remove/Create another widget
        # ----------------- Let's try to update
        new_af_response['properties'] = dict(
            statsConfig=dict(
                # Invalid IDS
                geoWidget=_get_widget_ID(Widget.WidgetType.GEO),
                severityWidget=_get_widget_ID(Widget.WidgetType.SCALE),
                reliabilityWidget=_get_widget_ID(Widget.WidgetType.SCALE),
                widget1d=_get_multiple_widget_ID(Widget.WidgetType.MATRIX1D),
                widget2d=_get_multiple_widget_ID(Widget.WidgetType.MATRIX2D),
                multiselectWidgets=_get_multiple_widget_ID(Widget.WidgetType.MULTISELECT),
                organigramWidgets=_get_multiple_widget_ID(Widget.WidgetType.ORGANIGRAM),
            ),
        )
        with self.captureOnCommitCallbacks(execute=True):
            response = _query_check(new_af_id, new_af_response, okay=True)
        self.assertMatchSnapshot(response, 'success')
        new_af = AnalysisFramework.objects.get(pk=new_af_id)
        self.assertMatchSnapshot(new_af.export.file.read().decode('utf-8'), 'success-af-export')
        # Check with conditionals
        other_af_widget = WidgetFactory.create(analysis_framework=AnalysisFrameworkFactory.create())
        af_widget = Widget.objects.filter(analysis_framework_id=new_af_id).first()
        af_widget_pk = af_widget and af_widget.pk

        # Some with conditionals
        new_af_response['primaryTagging'][0]['widgets'][1]['conditional'] = dict(
            parentWidget=other_af_widget.pk,
            conditions=[],
        )

        response = _query_check(new_af_id, new_af_response, okay=False)

        # Success Add
        new_af_response['primaryTagging'][0]['widgets'][1]['conditional'] = dict(
            parentWidget=af_widget_pk,
            conditions=[],
        )
        new_af_response['secondaryTagging'][0]['conditional'] = dict(
            parentWidget=af_widget_pk,
            conditions=[],
        )
        response = _query_check(new_af_id, new_af_response, okay=True)
        self.assertMatchSnapshot(response, 'with-conditionals-add')

        # Success Remove
        new_af_response['primaryTagging'][0]['widgets'][1].pop('conditional')
        new_af_response['secondaryTagging'][0]['conditional'] = None  # Should remove this only
        response = _query_check(new_af_id, new_af_response, okay=True)
        self.assertMatchSnapshot(response, 'with-conditionals-remove')

        # With another user (Access denied)
        another_user = UserFactory.create()
        self.force_login(another_user)
        _query_check(new_af_id, new_af_response, assert_for_error=True)

        # Project Log Check
        def _get_project_logs_qs(project):
            return ProjectChangeLog.objects.filter(project=project).order_by('id')

        assert _get_project_logs_qs(project3).count() == 0
        for project in [project1, project2]:
            project_log_qs = _get_project_logs_qs(project)
            assert project_log_qs.count() == 3
            assert list(project_log_qs.values_list('diff', flat=True)) == [
                dict(framework=dict(updated=True)),
            ] * 3

    def test_analysis_framework_membership_bulk(self):
        query = '''
          mutation MyMutation(
              $id: ID!,
              $afMembership: [BulkAnalysisFrameworkMembershipInputType!]!,
              $afMembershipDelete: [ID!]!
          ) {
          __typename
          analysisFramework(id: $id) {
            id
            title
            analysisFrameworkMembershipBulk(items: $afMembership, deleteIds: $afMembershipDelete) {
              errors
              result {
                id
                clientId
                joinedAt
                addedBy {
                  id
                  displayName
                }
                role {
                  id
                  title
                }
                member {
                  id
                  displayName
                }
              }
              deletedResult {
                id
                clientId
                joinedAt
                member {
                  id
                  displayName
                }
                role {
                  id
                  title
                }
                addedBy {
                  id
                  displayName
                }
              }
            }
          }
        }
        '''
        creater_user = UserFactory.create()
        user = UserFactory.create()
        low_permission_user = UserFactory.create()
        non_member_user = UserFactory.create()

        member_user1 = UserFactory.create()
        member_user2 = UserFactory.create()
        member_user3 = UserFactory.create()
        member_user4 = UserFactory.create()
        member_user5 = UserFactory.create()
        af = AnalysisFrameworkFactory.create(created_by=creater_user)
        membership1, _ = af.add_member(member_user1)
        membership2, _ = af.add_member(member_user2)
        af.add_member(member_user5)
        creater_user_membership, _ = af.add_member(creater_user, role=self.af_owner)
        user_membership, _ = af.add_member(user, role=self.af_owner)
        af.add_member(low_permission_user)

        minput = dict(
            afMembershipDelete=[
                str(membership1.pk),  # This will be only on try 1
                # This shouldn't be on any response (requester + creater)
                str(user_membership.pk),
                str(creater_user_membership.pk),
            ],
            afMembership=[
                # Try updating membership (Valid)
                dict(
                    member=member_user2.pk,
                    clientId="member-user-2",
                    role=self.af_owner.pk,
                    id=membership2.pk,
                ),
                # Try adding already existing member
                dict(
                    member=member_user5.pk,
                    clientId="member-user-5",
                    role=self.af_default.pk,
                ),
                # Try adding new member (Valid on try 1, invalid on try 2)
                dict(
                    member=member_user3.pk,
                    clientId="member-user-3",
                    role=self.af_default.pk,
                ),
                # Try adding new member (without giving role) -> this should use default role
                # Valid on try 1, invalid on try 2
                dict(
                    member=member_user4.pk,
                    clientId="member-user-4",
                ),
            ],
        )

        def _query_check(**kwargs):
            return self.query_check(
                query,
                mnested=['analysisFramework'],
                variables={'id': af.id, **minput},
                **kwargs,
            )
        # ---------- Without login
        _query_check(assert_for_error=True)
        # ---------- With login (with non-member)
        self.force_login(non_member_user)
        _query_check(assert_for_error=True)
        # ---------- With login (with low-permission member)
        self.force_login(non_member_user)
        _query_check(assert_for_error=True)
        # ---------- With login (with higher permission)
        self.force_login(user)
        # ----------------- Some Invalid input
        response = _query_check()['data']['analysisFramework']['analysisFrameworkMembershipBulk']
        self.assertMatchSnapshot(response, 'try 1')
        # ----------------- All valid input
        minput['afMembership'].pop(1)
        response = _query_check()['data']['analysisFramework']['analysisFrameworkMembershipBulk']
        self.assertMatchSnapshot(response, 'try 2')

    def test_analysis_framework_clone(self):
        query = '''
            mutation MyMutation ($id: ID!, $input: AnalysisFrameworkCloneInputType!) {
              __typename
              analysisFramework (id: $id ) {
                analysisFrameworkClone(data: $input) {
                  ok
                  errors
                  result {
                    id
                    title
                    description
                    clonedFrom
                  }
                }
              }
            }
        '''

        member_user = UserFactory.create()
        non_member_user = UserFactory.create()

        project = ProjectFactory.create()
        project.add_member(member_user)
        af = AnalysisFrameworkFactory.create(created_by=member_user, title='AF Orginal')
        af.add_member(member_user)

        minput = dict(
            title='AF (TEST)',
            description='Af description',
        )

        def _query_check(**kwargs):
            return self.query_check(
                query,
                minput=minput,
                mnested=['analysisFramework'],
                variables={'id': af.id},
                **kwargs,
            )

        # ---------- Without login
        _query_check(assert_for_error=True)
        # ---------- With login
        self.force_login(non_member_user)
        # ---------- Let's Clone a new AF (Using create test data)
        _query_check(assert_for_error=True)

        # ---------- With login (with access member)
        self.force_login(member_user)
        response = _query_check()
        self.assertMatchSnapshot(response, 'success')
        self.assertEqual(response['data']['analysisFramework']['analysisFrameworkClone']['result']['clonedFrom'], str(af.id))

        # adding project to the input
        minput['project'] = project.id

        # with Login (non project member)
        self.force_login(non_member_user)
        _query_check(assert_for_error=True)

        # With Login (project member)
        self.force_login(member_user)
        response = _query_check()['data']['analysisFramework']
        project.refresh_from_db()
        self.assertEqual(str(project.analysis_framework_id), response['analysisFrameworkClone']['result']['id'])

    @mock.patch('analysis_framework.serializers.AfWidgetLimit')
    def test_widgets_limit(self, AfWidgetLimitMock):
        query = '''
            mutation MyMutation ($input: AnalysisFrameworkInputType!) {
              __typename
              analysisFrameworkCreate(data: $input) {
                ok
                errors
                result {
                  id
                }
              }
            }
        '''

        user = UserFactory.create()

        minput = dict(
            title='AF (TEST)',
            primaryTagging=[
                dict(
                    title=f'Section {i}',
                    clientId=f'section-{i}',
                    order=i,
                    tooltip=f'Tooltip for section {i}',
                    widgets=[
                        dict(
                            clientId=f'section-text-{j}-client-id',
                            title=f'Section-Text-{j}',
                            widgetId=self.genum(Widget.WidgetType.TEXT),
                            version=1,
                            key=f'section-text-{j}',
                            order=j,
                        )
                        for j in range(0, 4)
                    ],
                ) for i in range(0, 2)
            ],
            secondaryTagging=[
                dict(
                    clientId=f'section-text-{j}-client-id',
                    title=f'Section-Text-{j}',
                    widgetId=self.genum(Widget.WidgetType.TEXT),
                    version=1,
                    key=f'section-text-{j}',
                    order=j,
                )
                for j in range(0, 4)
            ],
        )

        self.force_login(user)

        def _query_check(**kwargs):
            return self.query_check(query, minput=minput, **kwargs)['data']['analysisFrameworkCreate']

        # Let's change the limit to lower value for easy testing :P
        AfWidgetLimitMock.MAX_SECTIONS_ALLOWED = 1
        AfWidgetLimitMock.MAX_WIDGETS_ALLOWED_PER_SECTION = 2
        AfWidgetLimitMock.MAX_WIDGETS_ALLOWED_IN_SECONDARY_TAGGING = 2
        response = _query_check(okay=False)
        self.assertMatchSnapshot(response, 'failure-widget-level')
        # Let's change the limit to lower value for easy testing :P
        AfWidgetLimitMock.MAX_WIDGETS_ALLOWED_IN_SECONDARY_TAGGING = 10
        AfWidgetLimitMock.MAX_WIDGETS_ALLOWED_PER_SECTION = 10
        response = _query_check(okay=False)
        self.assertMatchSnapshot(response, 'failure-section-level')
        # Let's change the limit to higher value
        # Let's change the limit to higher value
        AfWidgetLimitMock.MAX_SECTIONS_ALLOWED = 5
        _query_check(okay=True)


class TestAnalysisFrameworkCreateUpdate(GraphQLTestCase):
    def setUp(self):
        super().setUp()
        self.user = UserFactory.create()
        self.create_mutation = '''
        mutation Mutation($input: AnalysisFrameworkInputType!) {
          analysisFrameworkCreate(data: $input) {
            ok
            errors
            result {
              id
              title
              isPrivate
              description
            }
          }
        }
        '''
        self.update_mutation = '''
        mutation UpdateMutation($input: AnalysisFrameworkInputType!, $id: ID!) {
            analysisFramework (id: $id ) {
              analysisFrameworkUpdate(data: $input) {
                ok
                errors
                result {
                  id
                  title
                  isPrivate
                  description
                }
              }
          }
        }
        '''

    def test_create_analysis_framework(self):
        self.input = dict(
            title='new title'
        )
        self.force_login(self.user)

        response = self.query(
            self.create_mutation,
            input_data=self.input
        )
        self.assertResponseNoErrors(response)

        content = response.json()
        self.assertTrue(content['data']['analysisFrameworkCreate']['ok'], content)
        self.assertEqual(
            content['data']['analysisFrameworkCreate']['result']['title'],
            self.input['title']
        )

    # TODO: MOVE THIS TO PROJECT TEST
    # def test_create_private_framework_unauthorized(self):
    #     project = ProjectFactory.create()
    #     project.add_member(self.user)
    #     self.input = dict(
    #         title='new title',
    #         isPrivate=True,
    #         project=project.id,
    #     )
    #     self.force_login(self.user)
    #     response = self.query(
    #         self.create_mutation,
    #         input_data=self.input
    #     )
    #     content = response.json()
    #     self.assertIsNotNone(content['errors'][0]['message'])
    #     # The actual message is
    #     # You don't have permissions to create private framework
    #     self.assertIn('permission', content['errors'][0]['message'])

    # def test_invalid_create_framework_privately_in_public_project(self):
    #     project = ProjectFactory.create(is_private=False)
    #     project.add_member(self.user)
    #     self.assertEqual(project.is_private, False)

    #     self.input = dict(
    #         title='new title',
    #         isPrivate=True,
    #         project=project.id,
    #     )
    #     self.force_login(self.user)

    #     response = self.query(
    #         self.create_mutation,
    #         input_data=self.input
    #     )
    #     content = response.json()
    #     self.assertIsNotNone(content['errors'][0]['message'])
    #     self.assertIn('permission', content['errors'][0]['message'])

    def test_change_is_private_field(self):
        """Even the owner should be unable to change privacy"""
        private_framework = AnalysisFrameworkFactory.create(is_private=True)
        public_framework = AnalysisFrameworkFactory.create(is_private=False)
        user = self.user
        private_framework.add_member(
            user,
            private_framework.get_or_create_owner_role()
        )
        public_framework.add_member(
            user,
            public_framework.get_or_create_owner_role()
        )
        content = self._change_framework_privacy(public_framework, user)
        self.assertIsNotNone(content['errors'][0]['message'])
        self.assertIn('permission', content['errors'][0]['message'])
        content = self._change_framework_privacy(private_framework, user)
        self.assertIsNotNone(content['errors'][0]['message'])
        self.assertIn('permission', content['errors'][0]['message'])

    def test_change_other_fields(self):
        private_framework = AnalysisFrameworkFactory.create(is_private=True)
        public_framework = AnalysisFrameworkFactory.create(is_private=False)
        user = self.user
        private_framework.add_member(
            user,
            private_framework.get_or_create_owner_role()
        )
        public_framework.add_member(
            user,
            public_framework.get_or_create_owner_role()
        )

        self.force_login(user)

        # private framework update
        self.input = dict(
            title='new title updated',
            isPrivate=private_framework.is_private,
        )
        response = self.query(
            self.update_mutation,
            input_data=self.input,
            variables={'id': private_framework.id},
        )
        private_framework.refresh_from_db()
        content = response.json()
        self.assertNotEqual(content['data']['analysisFramework']['analysisFrameworkUpdate'], None, content)
        self.assertTrue(content['data']['analysisFramework']['analysisFrameworkUpdate']['ok'], content)
        self.assertEqual(
            private_framework.title,
            self.input['title']
        )

        # public framework update
        self.input = dict(
            title='public title updated',
            isPrivate=public_framework.is_private,
        )
        response = self.query(
            self.update_mutation,
            input_data=self.input,
            variables={'id': public_framework.id},
        )
        public_framework.refresh_from_db()
        content = response.json()
        self.assertNotEqual(content['data']['analysisFramework']['analysisFrameworkUpdate'], None, content)
        self.assertTrue(content['data']['analysisFramework']['analysisFrameworkUpdate']['ok'], content)
        self.assertEqual(
            public_framework.title,
            self.input['title']
        )

    def _change_framework_privacy(self, framework, user):
        self.force_login(user)

        changed_privacy = not framework.is_private
        self.input = dict(
            title='new title',
            isPrivate=changed_privacy,
            # other fields not cared for now
        )
        response = self.query(
            self.update_mutation,
            input_data=self.input,
            variables={'id': framework.id},
        )
        content = response.json()
        return content

    def test_af_modified_at(self):
        create_mutation = '''
        mutation Mutation($input: AnalysisFrameworkInputType!) {
          analysisFrameworkCreate(data: $input) {
            ok
            errors
            result {
              id
              title
              isPrivate
              description
              modifiedAt
            }
          }
        }
        '''
        update_mutation = '''
        mutation UpdateMutation($input: AnalysisFrameworkInputType!, $id: ID!) {
            analysisFramework (id: $id ) {
              analysisFrameworkUpdate(data: $input) {
                ok
                errors
                result {
                  id
                  title
                  isPrivate
                  description
                  modifiedAt
                }
              }
          }
        }
        '''

        self.force_login(self.user)

        # Create
        minput = dict(title='new title')
        af_response = self.query_check(create_mutation, minput=minput)['data']['analysisFrameworkCreate']['result']
        af_id = af_response['id']
        af_modified_at = af_response['modifiedAt']

        # Update
        minput = dict(title='new updated title')
        updated_af_response = self.query_check(
            update_mutation, minput=minput, variables={'id': af_id}
        )['data']['analysisFramework']['analysisFrameworkUpdate']['result']
        # Make sure modifiedAt is higher now
        assert updated_af_response['modifiedAt'] > af_modified_at
