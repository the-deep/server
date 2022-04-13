from utils.graphene.tests import GraphQLTestCase

from organization.factories import (
    OrganizationTypeFactory,
    OrganizationFactory
)
from organization.models import OrganizationType, Organization
from user.factories import UserFactory


class TestOrganizationTypeQuery(GraphQLTestCase):
    def test_organization_type_query(self):
        query = '''
            query OrganizationType {
                organizationTypes {
                    results {
                        id
                        title
                        description
                        shortName
                    }
                    totalCount
                }
            }
        '''
        OrganizationType.objects.all().delete()
        OrganizationTypeFactory.create_batch(3)
        user = UserFactory.create()

        # Without authentication -----
        self.query_check(query, assert_for_error=True)

        self.force_login(user)
        content = self.query_check(query)
        self.assertEqual(len(content['data']['organizationTypes']['results']), 3, content)
        self.assertEqual(content['data']['organizationTypes']['totalCount'], 3, content)

    def test_organization_query(self):
        query = '''
            query MyQuery {
              organizations(search: "Organization-", ordering: DESC_TITLE) {
                results {
                  id
                  title
                }
                totalCount
              }
            }
        '''
        Organization.objects.all().delete()
        organizations = OrganizationFactory.create_batch(3)
        user = UserFactory.create()

        # Without authentication -----
        self.query_check(query, assert_for_error=True)

        self.force_login(user)
        content = self.query_check(query)
        self.assertEqual(len(content['data']['organizations']['results']), 3, content)
        self.assertEqual(
            [
                item['title'] for item in content['data']['organizations']['results']
            ],
            [
                org.title
                for org in organizations[::-1]
            ],
            content,
        )
        self.assertEqual(content['data']['organizations']['totalCount'], 3, content)

    def test_public_organizations_query(self):
        query = '''
            query PublicOrganizations {
                publicOrganizations {
                    results {
                        id
                        title
                    }
                    totalCount
                }
            }
        '''
        OrganizationFactory.create_batch(4)
        # should be visible without authentication
        content = self.query_check(query)
        self.assertEqual(content['data']['publicOrganizations']['totalCount'], 4, content)
