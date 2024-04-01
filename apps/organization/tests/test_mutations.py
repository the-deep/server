from user.factories import UserFactory
from utils.graphene.tests import GraphQLTestCase


class TestOrganizationMutation(GraphQLTestCase):
    CREATE_ORGANIZATION = '''
    mutation MyMutation ($input : OrganizationInputType!)
    {
        errors
        ok
        result {
          id
          longName
          shortName
          title
          url
      }
    }

    '''

    def setUp(self):
        super().setUp()
        self.member_user = UserFactory.create()

    def test_create_organization(self):
        def _query_check(minput, **kwargs):
            return self.query_check(
                self.CREATE_ORGANIZATION,
                minput=minput,
                **kwargs
            )
