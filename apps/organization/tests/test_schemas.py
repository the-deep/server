from lead.factories import LeadFactory
from organization.factories import OrganizationFactory, OrganizationTypeFactory
from organization.models import OrganizationType
from project.factories import ProjectFactory
from user.factories import UserFactory

from utils.graphene.tests import GraphQLTestCase


class TestOrganizationTypeQuery(GraphQLTestCase):
    def test_organization_type_query(self):
        query = """
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
        """
        OrganizationType.objects.all().delete()
        OrganizationTypeFactory.create_batch(3)
        user = UserFactory.create()

        # Without authentication -----
        self.query_check(query, assert_for_error=True)

        self.force_login(user)
        content = self.query_check(query)
        self.assertEqual(len(content["data"]["organizationTypes"]["results"]), 3, content)
        self.assertEqual(content["data"]["organizationTypes"]["totalCount"], 3, content)

    def test_organization_query(self):
        query = """
            query MyQuery (
                $verified: Boolean
                $search: String
                $usedInProjectByLead: ID
            ) {
              organizations(
                  search: $search
                  verified: $verified
                  usedInProjectByLead: $usedInProjectByLead
                  ordering: DESC_TITLE
              ) {
                results {
                  id
                  title
                }
                totalCount
              }
            }
        """
        org1 = OrganizationFactory.create(title="org-1", verified=False)
        org2 = OrganizationFactory.create(title="org-2", verified=True)
        org3 = OrganizationFactory.create(title="org-3", verified=False)
        org4 = OrganizationFactory.create(
            title="org-4",
            short_name="org-short-name-4",
            long_name="org-long-name-4",
            verified=True,
        )
        org5 = OrganizationFactory.create(title="org-5", verified=False)
        org6 = OrganizationFactory.create(title="org-5", verified=False)
        org7 = OrganizationFactory.create(title="órg-7", verified=False)
        all_org = [org7, org6, org5, org4, org3, org2, org1]
        user, non_member_user = UserFactory.create_batch(2)
        project = ProjectFactory.create()
        project.add_member(user)
        project.organizations.add(org5, org6)
        lead1, lead2, _ = LeadFactory.create_batch(3, project=project)

        lead1.source = org1
        lead1.authors.add(org2, org3)
        lead1.save()

        lead2.source = org3
        lead1.authors.add(org1, org3)
        lead2.save()

        for _user, filters, expected_organizations in [
            (user, {"search": "Organization-"}, [org7, org6, org5, org3, org2, org1]),
            (user, {"verified": True}, [org4, org2]),
            (user, {"verified": False}, [org7, org6, org5, org3, org1]),
            (
                user,
                {
                    "search": "Organization-",
                    "verified": True,
                },
                [org2],
            ),
            (
                user,
                {
                    "search": "Organization-",
                    "verified": False,
                },
                [org7, org6, org5, org3, org1],
            ),
            (
                user,
                {
                    "usedInProjectByLead": str(project.id),
                },
                [org6, org5, org3, org2, org1],
            ),
            (
                non_member_user,
                {
                    "usedInProjectByLead": str(project.id),
                    # Return all the organizations (Filter not applied)
                },
                all_org,
            ),
            # unaccent search
            (user, {"search": "org"}, all_org),
            (user, {"search": "órg"}, all_org),
            (user, {"search": "org-7"}, [org7]),
            (user, {"search": "órg-7"}, [org7]),
        ]:
            # Without authentication -----
            self.logout()
            self.query_check(query, variables=filters, assert_for_error=True)

            # With authentication
            self.force_login(_user)
            content = self.query_check(query, variables=filters)
            context = {
                "content": content,
                "user": _user,
                "filters": filters,
                "expected_organizations": expected_organizations,
            }

            self.assertEqual(len(content["data"]["organizations"]["results"]), len(expected_organizations), context)
            self.assertEqual(content["data"]["organizations"]["totalCount"], len(expected_organizations), context)
            self.assertEqual(
                [item["title"] for item in content["data"]["organizations"]["results"]],
                [org.title for org in expected_organizations],
                context,
            )

    def test_public_organizations_query(self):
        query = """
            query PublicOrganizations {
                publicOrganizations {
                    results {
                        id
                        title
                    }
                    totalCount
                }
            }
        """
        OrganizationFactory.create_batch(4)
        # should be visible without authentication
        content = self.query_check(query)
        self.assertEqual(content["data"]["publicOrganizations"]["totalCount"], 4, content)
