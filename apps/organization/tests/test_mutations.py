from user.factories import UserFactory
from utils.graphene.tests import GraphQLTestCase


class TestOrganizationMutation(GraphQLTestCase):
    def test_orgainization_query(self):
        self.organization_query = '''
        mutation MyMutation ($input : OrganizationInputType!)
        {
            organizationCreate(data: $input){
            errors
            ok
            result{
                id
                longName
                shortName
                title
                url
                verified
            }
        }
        }
    '''

        user = UserFactory.create()
        minput = dict(
            title="Test Organization",
            shortName="Short Name",
            longName="This is long name"
        )

        def _query_check(minput, **kwargs):
            return self.query_check(
                self.organization_query,
                minput=minput,
                **kwargs
            )
        # without login
        _query_check(minput, assert_for_error=True)

        # with login

        self.force_login(user)

        content = _query_check(minput)
        self.assertEqual(content['data']['organizationCreate']['errors'], None)
        self.assertEqual(content['data']['organizationCreate']['result']['title'], 'Test Organization')
        self.assertEqual(content['data']['organizationCreate']['result']['verified'], False)
