from utils.graphene.tests import GraphQLSnapShotTestCase

from unified_connector.models import ConnectorSource

from project.factories import ProjectFactory
from user.factories import UserFactory

# from unified_connector.factories import (
#     # ConnectorLeadFactory,
#     # ConnectorSourceLeadFactory,
#     ConnectorSourceFactory,
#     UnifiedConnectorFactory,
# )


class TestLeadMutationSchema(GraphQLSnapShotTestCase):
    factories_used = [ProjectFactory, UserFactory]

    CREATE_UNIFIED_CONNECTOR_QUERY = '''
        mutation MyMutation ($projectId: ID!, $input: UnifiedConnectorInputType!) {
          project(id: $projectId) {
            unifiedConnector {
              unifiedConnectorCreate(data: $input) {
                ok
                errors
                result {
                  id
                  clientId
                  isActive
                  project
                  title
                  sources {
                    id
                    clientId
                    params
                    source
                    title
                    unifiedConnector
                  }
                }
              }
            }
          }
        }
    '''

    def setUp(self):
        super().setUp()
        self.project = ProjectFactory.create()
        self.member_user = UserFactory.create()
        self.non_member_user = UserFactory.create()
        self.readonly_member_user = UserFactory.create()
        self.project.add_member(self.member_user)
        self.project.add_member(self.readonly_member_user, role=self.project_role_reader_non_confidential)

    def test_unified_connector_create(self):
        def _query_check(minput, **kwargs):
            return self.query_check(
                self.CREATE_UNIFIED_CONNECTOR_QUERY,
                minput=minput,
                variables={'projectId': self.project.id},
                **kwargs
            )

        minput = dict(
            title='unified-connector-s-1',
            clientId='u-connector-101',
            isActive=False,
            sources=[
                dict(
                    title='connector-s-1',
                    source=self.genum(ConnectorSource.Source.ATOM_FEED),
                    clientId='connecor-source-101',
                    params={
                        'sample-key': 'sample-value',
                    },
                ),
                dict(
                    title='connector-s-2',
                    source=self.genum(ConnectorSource.Source.RELIEF_WEB),
                    clientId='connecor-source-102',
                    params={
                        'sample-key': 'sample-value',
                    },
                ),
                dict(
                    title='connector-s-3',
                    # Same as previouse -> Throw error
                    source=self.genum(ConnectorSource.Source.RELIEF_WEB),
                    clientId='connecor-source-103',
                    params={
                        'sample-key': 'sample-value',
                    },
                )
            ]
        )

        # -- Without login
        _query_check(minput, assert_for_error=True)

        # -- With login (non-member)
        self.force_login(self.non_member_user)
        _query_check(minput, assert_for_error=True)

        # --- member user (read-only)
        self.force_login(self.readonly_member_user)
        _query_check(minput, assert_for_error=True)

        # --- member user (with error)
        self.force_login(self.member_user)
        _query_check(minput, okay=False)

        minput['sources'].pop(-1)
        # --- member user
        self.force_login(self.member_user)
        content = _query_check(minput)['data']['project']['unifiedConnector']['unifiedConnectorCreate']['result']
        self.assertMatchSnapshot(content, 'success')
