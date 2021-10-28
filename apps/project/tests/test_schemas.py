from dateutil.relativedelta import relativedelta

from django.utils import timezone
from django.contrib.gis.geos import Point

from utils.graphene.tests import GraphQLTestCase

from project.models import ProjectMembership, ProjectUserGroupMembership
from deep.permissions import ProjectPermissions as PP

from user.factories import UserFactory
from user_group.factories import UserGroupFactory
from lead.factories import LeadFactory
from entry.factories import EntryFactory
from project.factories import ProjectFactory, ProjectJoinRequestFactory
from analysis_framework.factories import AnalysisFrameworkFactory
from geo.factories import RegionFactory
from ary.factories import AssessmentTemplateFactory

from project.tasks import _generate_project_stats_cache


class TestProjectSchema(GraphQLTestCase):
    def test_project_query(self):
        """
        Test private + non-private project behaviour
        """
        query = '''
            query MyQuery ($id: ID!) {
              project(id: $id) {
                id
                title
                currentUserRole
                startDate
                status
                isVisualizationEnabled
                isPrivate
                endDate
                description
                data
                stats {
                  entriesActivity {
                    count
                    date
                  }
                  numberOfLeads
                  numberOfLeadsTagged
                  numberOfLeadsTaggedAndControlled
                  numberOfEntries
                  numberOfUsers
                  leadsActivity {
                    count
                    date
                  }
                }
                membershipPending
                regions {
                  id
                  title
                }
              }
            }
        '''

        user = UserFactory.create()
        public_project, public_project2, public_project3 = ProjectFactory.create_batch(3)
        analysis_framework = AnalysisFrameworkFactory.create()
        now = timezone.now()
        lead1_1 = self.update_obj(LeadFactory.create(project=public_project), created_at=now + relativedelta(months=-1))
        lead1_2 = self.update_obj(LeadFactory.create(project=public_project), created_at=now + relativedelta(months=-2))
        lead1_3 = self.update_obj(LeadFactory.create(project=public_project), created_at=now + relativedelta(months=-2))
        lead1_4 = self.update_obj(LeadFactory.create(project=public_project), created_at=now + relativedelta(months=-1))
        self.update_obj(LeadFactory.create(project=public_project), created_at=now + relativedelta(months=-1))

        data = [
            {
                "lead": lead1_1,
                "controlled": False,
                "months": -1,
            },
            {
                "lead": lead1_1,
                "controlled": False,
                "months": -3,
            },
            {
                "lead": lead1_2,
                "controlled": True,
                "months": -3,
            },
            {
                "lead": lead1_2,
                "controlled": False,
                "months": -2,
            },
            {
                "lead": lead1_2,
                "controlled": True,
                "months": -2,
            },
            {
                "lead": lead1_3,
                "controlled": True,
                "months": -3,
            },
            {
                "lead": lead1_3,
                "controlled": True,
                "months": -3,
            },

        ]
        now = timezone.now()
        for item in data:
            self.update_obj(
                EntryFactory.create(lead=item['lead'], controlled=item['controlled'],
                                    project=public_project, analysis_framework=analysis_framework),
                created_at=now + relativedelta(months=item['months'])
            )
        EntryFactory.create(lead=lead1_3, project=public_project, controlled=True, analysis_framework=analysis_framework)
        EntryFactory.create(lead=lead1_4, project=public_project, controlled=True, analysis_framework=analysis_framework)

        lead2 = LeadFactory.create(project=public_project2)
        lead3 = LeadFactory.create(project=public_project3)
        EntryFactory.create(lead=lead2, project=public_project2, controlled=False, analysis_framework=analysis_framework)
        EntryFactory.create(lead=lead3, project=public_project3, controlled=False, analysis_framework=analysis_framework)

        user2, user3, request_user, non_member_user = UserFactory.create_batch(4)
        analysis_framework = AnalysisFrameworkFactory.create()
        public_project = ProjectFactory.create()
        private_project = ProjectFactory.create(is_private=True)
        ProjectJoinRequestFactory.create(
            project=public_project, requested_by=request_user,
            status='pending', role=self.project_role_admin
        )

        # add some project member
        public_project.add_member(user)
        public_project.add_member(user2)
        public_project.add_member(user3)

        # add some lead for the project
        lead = LeadFactory.create(project=public_project)
        LeadFactory.create_batch(3, project=public_project)
        LeadFactory.create(project=private_project)

        # add some entry for the project
        EntryFactory.create_batch(
            4,
            project=public_project, analysis_framework=analysis_framework, lead=lead
        )
        EntryFactory.create(project=private_project, analysis_framework=analysis_framework, lead=lead)

        # lets add some regions to project
        region1, region2, region3 = RegionFactory.create_batch(3)
        public_project.regions.add(region1)
        public_project.regions.add(region2)
        private_project.regions.add(region3)

        # Generate project cache
        _generate_project_stats_cache()

        # -- Without login
        self.query_check(query, assert_for_error=True, variables={'id': public_project.id})
        self.query_check(query, assert_for_error=True, variables={'id': private_project.id})

        # -- With login
        self.force_login(user)

        # --- non-member user
        content = self.query_check(query, variables={'id': public_project.id})
        self.assertNotEqual(content['data']['project'], None, content)
        content = self.query_check(query, variables={'id': private_project.id})
        self.assertEqual(content['data']['project'], None, content)

        # login with non_member
        self.force_login(non_member_user)
        content = self.query_check(query, variables={'id': public_project.id})
        self.assertNotEqual(content['data']['project'], None, content)
        self.assertEqual(content['data']['project']['membershipPending'], False)

        # --- member user
        # ---- (public-project)
        self.force_login(user)
        content = self.query_check(query, variables={'id': public_project.id})
        self.assertNotEqual(content['data']['project'], None, content)
        self.assertEqual(content['data']['project']['stats']['numberOfLeads'], 4, content)
        self.assertEqual(content['data']['project']['stats']['numberOfLeadsTagged'], 1, content)
        self.assertEqual(content['data']['project']['stats']['numberOfLeadsTaggedAndControlled'], 0, content)
        self.assertEqual(content['data']['project']['stats']['numberOfEntries'], 4, content)
        self.assertEqual(content['data']['project']['stats']['numberOfUsers'], 3, content)
        self.assertEqual(len(content['data']['project']['stats']['leadsActivity']), 1, content)
        self.assertEqual(len(content['data']['project']['stats']['entriesActivity']), 1, content)
        self.assertEqual(len(content['data']['project']['regions']), 2, content)
        self.assertListIds(content['data']['project']['regions'], [region1, region2], content)

        # login with request user
        self.force_login(request_user)
        content = self.query_check(query, variables={'id': public_project.id})
        self.assertNotEqual(content['data']['project'], None, content)
        self.assertEqual(content['data']['project']['membershipPending'], True)

        # ---- (private-project)
        self.force_login(user)
        private_project.add_member(user)
        content = self.query_check(query, variables={'id': private_project.id})
        self.assertNotEqual(content['data']['project'], None, content)
        self.assertEqual(len(content['data']['project']['regions']), 1, content)
        self.assertListIds(content['data']['project']['regions'], [region3], content)

    def test_project_query_has_assesment_af(self):
        query = '''
            query MyQuery {
              projects(ordering: "id") {
                  results {
                    id
                    hasAnalysisFramework
                    hasAssessmentTemplate
                  }
              }
            }
        '''
        user = UserFactory.create()
        analysis_framework = AnalysisFrameworkFactory.create()
        assessment_template = AssessmentTemplateFactory.create()
        project1 = ProjectFactory.create(analysis_framework=analysis_framework, assessment_template=assessment_template)
        project2 = ProjectFactory.create(analysis_framework=analysis_framework,)
        project3 = ProjectFactory.create(assessment_template=assessment_template)
        self.force_login(user)

        projects = self.query_check(query)['data']['projects']['results']
        for index, (_id, has_af, has_ary_template) in enumerate([
            (project1.pk, True, True),
            (project2.pk, True, False),
            (project3.pk, False, True),
        ]):
            self.assertIdEqual(projects[index]['id'], _id, projects)
            self.assertEqual(projects[index]['hasAnalysisFramework'], has_af, projects)
            self.assertEqual(projects[index]['hasAssessmentTemplate'], has_ary_template, projects)

    def test_projects_query(self):
        """
        Test private + non-private project list behaviour
        """
        query = '''
            query MyQuery {
              projects (ordering: "id") {
                page
                pageSize
                totalCount
                results {
                  id
                  status
                  title
                  isPrivate
                  description
                  currentUserRole
                }
              }
            }
        '''

        user = UserFactory.create()
        public_project = ProjectFactory.create()
        private_project = ProjectFactory.create(is_private=True)

        # -- Without login
        self.query_check(query, assert_for_error=True)

        # -- With login
        self.force_login(user)

        # --- non-member user (only public project is listed)
        content = self.query_check(query)
        self.assertEqual(content['data']['projects']['totalCount'], 1, content)
        self.assertEqual(content['data']['projects']['results'][0]['id'], str(public_project.pk), content)

        # --- member user (all public project is listed)
        public_project.add_member(user)
        private_project.add_member(user)
        content = self.query_check(query)
        self.assertEqual(content['data']['projects']['totalCount'], 2, content)
        self.assertEqual(content['data']['projects']['results'][0]['id'], str(public_project.pk), content)
        self.assertEqual(content['data']['projects']['results'][1]['id'], str(private_project.pk), content)

    def test_project_stat_recent(self):
        query = '''
              query MyQuery {
                recentProjects {
                  id
                  status
                  title
                  isPrivate
                  description
                  currentUserRole
                }
              }
          '''

        user = UserFactory.create()
        analysis_framework = AnalysisFrameworkFactory.create()
        public_project1, public_project2, public_project3, public_project4 = ProjectFactory.create_batch(4)
        public_project1.add_member(user)
        public_project2.add_member(user)
        public_project3.add_member(user)

        lead1 = LeadFactory.create(project=public_project1, created_by=user)
        LeadFactory.create(project=public_project2, created_by=user)
        EntryFactory.create(lead=lead1, controlled=False,
                            created_by=user, project=public_project1,
                            analysis_framework=analysis_framework)
        LeadFactory.create(project=public_project3, created_by=user)
        LeadFactory.create(project=public_project4, created_by=user)
        # -- Without login
        self.query_check(query, assert_for_error=True)

        # -- With login
        self.force_login(user)

        content = self.query_check(query)
        self.assertEqual(len(content['data']['recentProjects']), 3, content)
        self.assertEqual(content['data']['recentProjects'][0]['id'], str(public_project3.pk), content)
        self.assertEqual(content['data']['recentProjects'][1]['id'], str(public_project1.pk), content)
        self.assertEqual(content['data']['recentProjects'][2]['id'], str(public_project2.pk), content)

    def test_project_allowed_permissions(self):
        query = '''
              query MyQuery {
                projects {
                  results {
                   id
                   allowedPermissions
                  }
                }
              }
        '''
        project1, project2 = ProjectFactory.create_batch(2)
        user = UserFactory.create()
        project1.add_member(user, badges=[])
        project2.add_member(user, badges=[ProjectMembership.BadgeType.QA])

        self.force_login(user)
        content_projects = self.query_check(query)['data']['projects']['results']
        QA_PERMISSION = self.genum(PP.Permission.CAN_QUALITY_CONTROL)
        content_projects_permissions = {
            int(pdata['id']): pdata['allowedPermissions']
            for pdata in content_projects
        }
        self.assertEqual(len(content_projects), 2, content_projects)
        self.assertNotIn(QA_PERMISSION, content_projects_permissions[project1.pk], content_projects)
        self.assertIn(QA_PERMISSION, content_projects_permissions[project2.pk], content_projects)

    def test_projects_by_region(self):
        query = '''
            query MyQuery {
              projectsByRegion {
               id
               projectsId
                centroid
              }
            }
        '''
        user = UserFactory.create()
        region1 = RegionFactory.create()
        region2 = RegionFactory.create()
        project1 = ProjectFactory.create(regions=[region1])
        project2 = ProjectFactory.create(is_private=True, regions=[region1, region2])
        # This two projects willn't be shown
        ProjectFactory.create(is_private=True, regions=[region1, region2])  # private + no member access
        ProjectFactory.create()  # no regions attached
        project2.add_member(user)
        self.force_login(user)

        content = self.query_check(query)['data']['projectsByRegion']
        self.assertEqual(content, [], content)

        # only save region2 centroid.
        region2.centroid = Point(1, 2)
        region2.save(update_fields=('centroid',))
        content = self.query_check(query)['data']['projectsByRegion']
        self.assertEqual(
            content, [
                {
                    'id': str(region2.pk),
                    'centroid': {
                        'coordinates': [region2.centroid.x, region2.centroid.y],
                        'type': 'Point'
                    },
                    'projectsId': [str(project2.pk)]
                }
            ], content)

        # Now save region1 centroid as well.
        region1.centroid = Point(2, 3)
        region1.save(update_fields=('centroid',))
        content = self.query_check(query)['data']['projectsByRegion']
        self.assertEqual(
            content, [
                {
                    'id': str(region2.pk),
                    'centroid': {
                        'coordinates': [region2.centroid.x, region2.centroid.y],
                        'type': 'Point'
                    },
                    'projectsId': [str(project2.pk)]
                }, {
                    'id': str(region1.pk),
                    'centroid': {
                        'coordinates': [region1.centroid.x, region1.centroid.y],
                        'type': 'Point'
                    },
                    'projectsId': [str(project1.pk), str(project2.pk)]
                }

            ], content)


class TestProjectFilterSchema(GraphQLTestCase):
    def test_project_query_filter(self):
        query = '''
            query MyQuery ($isCurrentUserMember: Boolean!) {
              projects(isCurrentUserMember: $isCurrentUserMember) {
                page
                pageSize
                totalCount
                results {
                  id
                  title
                  isPrivate
                  currentUserRole
                }
              }
            }
        '''

        user = UserFactory.create()
        project1 = ProjectFactory.create()
        project2 = ProjectFactory.create(is_private=True)
        project3 = ProjectFactory.create()
        ProjectFactory.create(is_private=True)

        # Add user to project1 only (one normal + one private)
        project1.add_member(user)
        project2.add_member(user)

        # -- Without login
        self.query_check(query, variables={'isCurrentUserMember': True}, assert_for_error=True)

        # -- With login
        self.force_login(user)

        # project without membership
        content = self.query_check(query, variables={'isCurrentUserMember': True})
        self.assertEqual(content['data']['projects']['totalCount'], 2, content)
        self.assertListIds(content['data']['projects']['results'], [project1, project2], content)
        # project with membership
        content = self.query_check(query, variables={'isCurrentUserMember': False})
        self.assertEqual(content['data']['projects']['totalCount'], 1, content)  # Private will not show here
        self.assertListIds(content['data']['projects']['results'], [project3], content)


class TestProjectMembersFilterSchema(GraphQLTestCase):
    def test_project(self):
        query = '''
            query MyQuery ($id: ID!, $user_search: String, $usergroup_search: String) {
              project(id: $id) {
                userMembers(search: $user_search) {
                  totalCount
                  results {
                    member {
                      id
                      displayName
                    }
                    role {
                      id
                      level
                      title
                    }
                  }
                }
                userGroupMembers(search: $usergroup_search) {
                  totalCount
                  results {
                    id
                    usergroup {
                      id
                      title
                    }
                    role {
                      id
                      level
                      title
                    }
                    badges
                  }
                }
              }
            }
        '''

        user, user1, user2, user3, _ = UserFactory.create_batch(5, first_name='Ram')
        usergroup1, usergroup2, _ = UserGroupFactory.create_batch(3, title='UserGroup YYY')
        usergroup4 = UserGroupFactory.create(title='UserGroup ZZZ')

        user5 = UserFactory.create(first_name='Nam')
        project = ProjectFactory.create()

        # Add user to project1 only (one normal + one private)
        project.add_member(user)
        project.add_member(user1)
        project.add_member(user2)
        project.add_member(user3)
        project.add_member(user5)

        for usergroup in [usergroup1, usergroup2, usergroup4]:
            ProjectUserGroupMembership.objects.create(project=project, usergroup=usergroup)

        # -- With login
        self.force_login(user)

        # project without membership
        content = self.query_check(query, variables={'id': project.id, 'user_search': user.first_name})
        self.assertEqual(content['data']['project']['userMembers']['totalCount'], 4, content)
        self.assertEqual(len(content['data']['project']['userMembers']['results']), 4, content)
        self.assertEqual(content['data']['project']['userGroupMembers']['totalCount'], 3, content)
        self.assertEqual(len(content['data']['project']['userGroupMembers']['results']), 3, content)

        # project without membership
        content = self.query_check(query, variables={'id': project.id, 'usergroup_search': usergroup1.title})
        self.assertEqual(content['data']['project']['userGroupMembers']['totalCount'], 2, content)
        self.assertEqual(len(content['data']['project']['userGroupMembers']['results']), 2, content)
        self.assertEqual(content['data']['project']['userMembers']['totalCount'], 5, content)
        self.assertEqual(len(content['data']['project']['userMembers']['results']), 5, content)
