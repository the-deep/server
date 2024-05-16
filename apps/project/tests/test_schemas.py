import pytz
from datetime import datetime
from dateutil.relativedelta import relativedelta
from unittest.mock import patch

from django.utils import timezone
from django.contrib.gis.geos import Point
from django.core.cache import cache

from utils.graphene.tests import GraphQLTestCase, GraphQLSnapShotTestCase

from lead.models import Lead
from project.models import (
    ProjectMembership,
    ProjectUserGroupMembership,
    ProjectStats,
    Project,
    ProjectRole,
)
from deep.permissions import ProjectPermissions as PP
from deep.caches import CacheKey
from deep.trackers import schedule_tracker_data_handler

from user.factories import UserFactory
from user_group.factories import UserGroupFactory
from lead.factories import LeadFactory
from entry.factories import EntryFactory
from project.factories import ProjectFactory, ProjectJoinRequestFactory, ProjectPinnedFactory
from analysis_framework.factories import AnalysisFrameworkFactory
from geo.factories import RegionFactory, AdminLevelFactory, GeoAreaFactory
from ary.factories import AssessmentTemplateFactory
from export.factories import ExportFactory
from quality_assurance.factories import EntryReviewCommentFactory

from project.tasks import _generate_project_stats_cache
from geo.enums import GeoAreaOrderingEnum

from .test_mutations import TestProjectGeneralMutationSnapshotTest


class TestProjectSchema(GraphQLTestCase):
    def test_project_recent_activities(self):
        query = '''
           query MyQuery {
                recentActivities {
                    createdAt
                    id
                    type
                    typeDisplay
                    createdBy {
                        id
                        isActive
                        emailDisplay
                        displayName
                        firstName
                        lastName
                        profile {
                            displayPictureUrl
                            organization
                        }
                    }
                    project {
                        id
                        startDate
                        endDate
                        description
                        status
                        statusDisplay
                        title
                    }
                    leadId
                }
            }
        '''
        normal_user, member_user = UserFactory.create_batch(2)

        af = AnalysisFrameworkFactory.create()
        project = ProjectFactory.create(analysis_framework=af, created_by=member_user)
        project.add_member(member_user)

        # Leads
        lead1 = LeadFactory(project=project, created_by=member_user)
        LeadFactory.create_batch(2, project=project, created_by=member_user)

        # Entries
        EntryFactory.create_batch(7, lead=lead1, project=project, created_by=member_user)
        entry = EntryFactory(lead=lead1, project=project, created_by=member_user)

        # Entries Comments
        EntryReviewCommentFactory(entry=entry, created_by=member_user)

        self.force_login(normal_user)
        response = self.query_check(query)
        self.assertEqual(len(response['data']['recentActivities']), 0)

        self.force_login(member_user)
        response = self.query_check(query)
        self.assertEqual(len(response['data']['recentActivities']), 12)

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
                  numberOfLeadsNotTagged
                  numberOfLeadsInProgress
                  numberOfLeadsTagged
                  numberOfEntries
                  numberOfEntriesVerified
                  numberOfEntriesControlled
                  numberOfUsers
                  leadsActivity {
                    count
                    date
                  }
                }
                membershipPending
                isRejected
                regions {
                  id
                  title
                }
              }
            }
        '''

        user = UserFactory.create()
        analysis_framework = AnalysisFrameworkFactory.create()
        public_project, public_project2, public_project3, public_project4 = ProjectFactory.create_batch(
            4,
            analysis_framework=analysis_framework
        )
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
        public_project = ProjectFactory.create(analysis_framework=analysis_framework)
        private_project = ProjectFactory.create(is_private=True, analysis_framework=analysis_framework)
        ProjectJoinRequestFactory.create(
            project=public_project, requested_by=request_user,
            status='pending', role=self.project_role_admin
        )
        # create projectJoinRequest(status='rejected')
        ProjectJoinRequestFactory.create(
            project=public_project4, requested_by=request_user,
            status='rejected', role=self.project_role_admin
        )
        # add some project member
        public_project.add_member(user)
        public_project.add_member(user2)
        public_project.add_member(user3)

        # add some lead for the project
        lead = LeadFactory.create(project=public_project)
        lead2 = LeadFactory.create(project=public_project)
        LeadFactory.create_batch(3, project=public_project)
        LeadFactory.create(project=private_project)

        # add some entry for the project
        EntryFactory.create_batch(
            4,
            project=public_project, analysis_framework=analysis_framework, lead=lead
        )
        entry2_1 = EntryFactory.create(
            project=public_project, analysis_framework=analysis_framework, lead=lead2, controlled=True)
        entry2_2 = EntryFactory.create(project=public_project, analysis_framework=analysis_framework, lead=lead2)
        EntryFactory.create(project=private_project, analysis_framework=analysis_framework, lead=lead)

        # Verify entries
        entry2_1.verified_by.add(user)
        entry2_1.verified_by.add(user3)
        entry2_2.verified_by.add(user)

        # NOTE: Right noe only IN_PROGRESS status is set automatically
        # Control one lead
        lead2.status = Lead.Status.TAGGED
        lead2.save(update_fields=('status',))

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

        # login with request_user
        self.force_login(request_user)
        content = self.query_check(query, variables={'id': public_project4.id})
        self.assertNotEqual(content['data']['project'], None, content)
        self.assertEqual(content['data']['project']['isRejected'], True)

        # --- member user
        # ---- (public-project)
        self.force_login(user)
        content = self.query_check(query, variables={'id': public_project.id})
        self.assertNotEqual(content['data']['project'], None, content)
        self.assertEqual(content['data']['project']['stats']['numberOfLeads'], 5, content)
        self.assertEqual(content['data']['project']['stats']['numberOfLeadsNotTagged'], 3, content)
        self.assertEqual(content['data']['project']['stats']['numberOfLeadsInProgress'], 1, content)
        self.assertEqual(content['data']['project']['stats']['numberOfLeadsTagged'], 1, content)
        self.assertEqual(content['data']['project']['stats']['numberOfEntries'], 6, content)
        self.assertEqual(content['data']['project']['stats']['numberOfEntriesVerified'], 2, content)
        self.assertEqual(content['data']['project']['stats']['numberOfEntriesControlled'], 1, content)
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
              projects(ordering: ASC_TITLE) {
                  results {
                    id
                    hasAnalysisFramework
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
        for index, (_id, has_af) in enumerate([
            (project1.pk, True),
            (project2.pk, True),
            (project3.pk, False),
        ]):
            self.assertIdEqual(projects[index]['id'], _id, projects)
            self.assertEqual(projects[index]['hasAnalysisFramework'], has_af, projects)

    def test_projects_query(self):
        """
        Test private + non-private project list behaviour
        """
        query = '''
            query MyQuery {
              projects (ordering: ASC_TITLE) {
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

    def test_public_projects(self):
        query = '''
            query MyQuery {
              publicProjects (ordering: ASC_TITLE) {
                page
                pageSize
                totalCount
                results {
                  id
                  title
                  description
                  createdAt
                  analysisFrameworkTitle
                  organizationsTitle
                  regionsTitle
                  numberOfEntries
                  numberOfLeads
                  numberOfUsers
                }
              }
            }
        '''
        # Lets create some analysis_framework(private + publice)
        public_af = AnalysisFrameworkFactory.create(
            is_private=False,
            title='Public Analysis Framework Title'
        )
        private_af = AnalysisFrameworkFactory.create(
            title='Private Analysis Framework Title',
            is_private=True
        )

        # lets create some regions(private + public)
        public_region = RegionFactory.create(public=True, title='Public Region')
        private_region = RegionFactory.create(public=False, title='Private Region')
        # deleted_project
        ProjectFactory.create(analysis_framework=public_af, regions=[public_region], is_deleted=True)
        public_project1 = ProjectFactory.create(analysis_framework=public_af, regions=[public_region])
        public_project2 = ProjectFactory.create(analysis_framework=public_af, regions=[private_region])
        public_project3 = ProjectFactory.create(analysis_framework=private_af, regions=[public_region])
        public_project4 = ProjectFactory.create(analysis_framework=private_af, regions=[public_region])
        private_project = ProjectFactory.create(is_private=True)
        content = self.query_check(query)
        self.assertEqual(content['data']['publicProjects']['totalCount'], 4, content)
        self.assertListIds(
            content['data']['publicProjects']['results'],
            [public_project1, public_project2, public_project3, public_project4],
            content
        )
        # some checks for analysis_framework private and public
        self.assertEqual(
            content['data']['publicProjects']['results'][0]['analysisFrameworkTitle'],
            'Public Analysis Framework Title',
            content
        )
        self.assertEqual(
            content['data']['publicProjects']['results'][2]['analysisFrameworkTitle'],
            None,
            content
        )
        # some check for regions private and public
        self.assertEqual(
            content['data']['publicProjects']['results'][2]['regionsTitle'],
            'Public Region',
            content
        )
        self.assertEqual(
            content['data']['publicProjects']['results'][1]['regionsTitle'],
            '',
            content
        )
        # make sure private projects are not visible here
        self.assertNotListIds(content['data']['publicProjects']['results'], [private_project], content)

    def test_project_geoareas(self):
        query = '''
              query MyQuery(
                  $projectID: ID!,
                  $ids: [ID!],
                  $ordering: [GeoAreaOrderingEnum!],
                  $search: String,
                  $titles: [String!]
              ) {
                project(id: $projectID) {
                    geoAreas(
                        ids: $ids,
                        ordering: $ordering,
                        search: $search,
                        titles: $titles
                    ) {
                        totalCount
                        results {
                            id
                            adminLevelTitle
                            regionTitle
                            title
                        }
                    }
                }
              }
          '''

        user = UserFactory.create()
        region = RegionFactory.create(title='Nepal', is_published=True)
        project = ProjectFactory.create()
        project.add_member(user)
        project.regions.add(region)

        admin_level = AdminLevelFactory.create(title='District', region=region)
        geo1 = GeoAreaFactory.create(admin_level=admin_level, title='Kathmandu')
        geo2 = GeoAreaFactory.create(admin_level=admin_level, title='Lalitpur')
        GeoAreaFactory.create(admin_level=admin_level, title='Bhaktapur')

        geo1_data = dict(
            id=str(geo1.pk),
            adminLevelTitle=geo1.admin_level.title,
            regionTitle=geo1.admin_level.region.title,
            title=geo1.title,
        )
        geo2_data = dict(
            id=str(geo2.pk),
            adminLevelTitle=geo2.admin_level.title,
            regionTitle=geo2.admin_level.region.title,
            title=geo2.title,
        )

        def _query_check(variables={}, **kwargs):
            return self.query_check(
                query,
                variables={'projectID': project.id, **variables},
                **kwargs,
            )

        # -- Without login
        _query_check(assert_for_error=True)

        # -- With login
        self.force_login(user)

        content = _query_check()['data']['project']['geoAreas']['results']
        self.assertEqual(len(content), 3, content)

        filters = {'ids': [str(geo1.pk), str(geo2.pk)], 'ordering': self.genum(GeoAreaOrderingEnum.ASC_ID)}
        content = _query_check(variables=filters)['data']['project']['geoAreas']['results']
        self.assertEqual(len(content), 2, content)
        self.assertEqual(content, [geo1_data, geo2_data], content)

        filters = {'search': 'kathm', 'ordering': self.genum(GeoAreaOrderingEnum.ASC_ID)}
        content = _query_check(variables=filters)['data']['project']['geoAreas']['results']
        self.assertEqual(len(content), 1, content)
        self.assertEqual(content, [geo1_data], content)

        filters = {'titles': ['Kathmandu', 'lalitpur'], 'ordering': self.genum(GeoAreaOrderingEnum.ASC_ID)}
        content = _query_check(variables=filters)['data']['project']['geoAreas']['results']
        self.assertEqual(len(content), 2, content)
        self.assertEqual(content, [geo1_data, geo2_data], content)

        filters = {'titles': ['Kath', 'lal'], 'ordering': self.genum(GeoAreaOrderingEnum.ASC_ID)}
        content = _query_check(variables=filters)['data']['project']['geoAreas']['results']
        self.assertEqual(len(content), 0, content)
        self.assertEqual(content, [], content)

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
            query MyQuery ($projectFilter: RegionProjectFilterData) {
              projectsByRegion (projectFilter: $projectFilter) {
               totalCount
               results {
                 id
                 projectsId
                 centroid
               }
              }
            }
        '''
        user = UserFactory.create()
        region1 = RegionFactory.create()
        region2 = RegionFactory.create()
        project1 = ProjectFactory.create(regions=[region1], title='Test Nepal')
        project2 = ProjectFactory.create(is_private=True, regions=[region1, region2], title='Test USA')
        # This two projects willn't be shown
        ProjectFactory.create(is_private=True, regions=[region1, region2])  # private + no member access
        ProjectFactory.create()  # no regions attached
        project2.add_member(user)
        self.force_login(user)

        content = self.query_check(query)['data']['projectsByRegion']['results']
        self.assertEqual(content, [], content)

        # only save region2 centroid.
        region2.centroid = Point(1, 2)
        region2.save(update_fields=('centroid',))
        content = self.query_check(query)['data']['projectsByRegion']
        self.assertEqual(content['totalCount'], 1, content)
        self.assertEqual(
            content['results'], [
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
        self.assertEqual(content['totalCount'], 2, content)
        self.assertEqual(
            content['results'], [
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

        # Now using filters
        project_filter = {'search': 'USA'}
        content = self.query_check(query, variables={'projectFilter': project_filter})['data']['projectsByRegion']
        self.assertEqual(content['totalCount'], 2, content)
        self.assertEqual(
            content['results'], [
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
                    'projectsId': [str(project2.pk)]
                }
            ], content)

        project_filter = {'ids': [project1.pk]}
        content = self.query_check(query, variables={'projectFilter': project_filter})['data']['projectsByRegion']
        self.assertEqual(content['totalCount'], 1, content)
        self.assertEqual(
            content['results'], [
                {
                    'id': str(region1.pk),
                    'centroid': {
                        'coordinates': [region1.centroid.x, region1.centroid.y],
                        'type': 'Point'
                    },
                    'projectsId': [str(project1.pk)]
                }
            ], content)

    def test_public_projects_by_region(self):
        query = '''
            query MyQuery ($projectFilter: RegionProjectFilterData) {
              publicProjectsByRegion (projectFilter: $projectFilter) {
               totalCount
               results {
                 id
                 projectsId
                 centroid
               }
              }
            }
        '''
        fake_centroid = Point(1, 2)
        region1 = RegionFactory.create(public=False, centroid=fake_centroid)
        region2 = RegionFactory.create(centroid=fake_centroid)
        region3 = RegionFactory.create(centroid=fake_centroid)
        region4 = RegionFactory.create(public=False, centroid=fake_centroid)
        RegionFactory.create()  # No Centroid ( This will not show)
        # Deleted project
        ProjectFactory.create(is_private=False, is_deleted=True, regions=[region1, region2], title='Test Nepal')
        project1 = ProjectFactory.create(is_private=False, regions=[region1, region2], title='Test Nepal')
        ProjectFactory.create(is_private=False, regions=[region3], title='Test Canada')
        project2 = ProjectFactory.create(is_private=True, regions=[region4], title='Test Brazil')

        def _query_check(project_filter):
            return self.query_check(query, variables={'projectFilter': project_filter})

        content = self.query_check(query)
        self.assertEqual(content['data']['publicProjectsByRegion']['totalCount'], 3, content)

        # test for project filter
        content = _query_check({'ids': [project1.pk]})['data']['publicProjectsByRegion']
        self.assertEqual(content['totalCount'], 2, content)

        content = _query_check({'ids': [project1.pk, project2.pk]})['data']['publicProjectsByRegion']
        self.assertEqual(content['totalCount'], 2, content)

        content = _query_check({'search': 'Canada'})['data']['publicProjectsByRegion']
        self.assertEqual(content['totalCount'], 1, content)

        content = _query_check({'search': 'Brazil'})['data']['publicProjectsByRegion']
        self.assertEqual(content['totalCount'], 0, content)  # Private projects are not shown

    def test_project_stats_with_filter(self):
        query = '''
            query MyQuery ($projectId: ID! $leadFilters: LeadsFilterDataInputType) {
              project(id: $projectId) {
                stats(filters: $leadFilters) {
                  filteredNumberOfEntries
                  filteredNumberOfEntriesControlled
                  filteredNumberOfEntriesVerified
                  filteredNumberOfLeads
                  filteredNumberOfLeadsInProgress
                  filteredNumberOfLeadsNotTagged
                  filteredNumberOfLeadsTagged
                  numberOfEntries
                  numberOfEntriesControlled
                  numberOfEntriesVerified
                  numberOfLeads
                  numberOfLeadsInProgress
                  numberOfLeadsNotTagged
                  numberOfLeadsTagged
                  numberOfUsers
                }
              }
            }
        '''

        non_member_user, member_user = UserFactory.create_batch(2)
        af = AnalysisFrameworkFactory.create()
        project = ProjectFactory.create(analysis_framework=af)
        project.add_member(member_user)
        lead1 = LeadFactory.create(project=project, confidentiality=Lead.Confidentiality.CONFIDENTIAL)
        lead2 = LeadFactory.create(project=project, status=Lead.Status.TAGGED)
        EntryFactory.create_batch(2, lead=lead1, controlled=True)
        EntryFactory.create(lead=lead2, verified_by=[member_user])
        lead2.status = Lead.Status.TAGGED
        lead2.save(update_fields=('status',))

        def _query_check(filters=None, **kwargs):
            return self.query_check(
                query,
                variables={
                    'projectId': project.id,
                    'leadFilters': filters,
                },
                **kwargs
            )

        def _expected_response(
            filtered_number_of_leads,
            filtered_number_of_leadsInProgress,
            filtered_number_of_leadsNotTagged,
            filtered_number_of_leadsTagged,
            filtered_number_of_entries,
            filtered_number_of_entriesControlled,
            filtered_number_of_entriesVerified,
        ):
            return dict(
                numberOfUsers=1,
                numberOfEntries=3,
                numberOfEntriesControlled=2,
                numberOfEntriesVerified=1,
                numberOfLeads=2,
                numberOfLeadsInProgress=1,
                numberOfLeadsNotTagged=0,
                numberOfLeadsTagged=1,
                filteredNumberOfEntries=filtered_number_of_entries,
                filteredNumberOfEntriesControlled=filtered_number_of_entriesControlled,
                filteredNumberOfEntriesVerified=filtered_number_of_entriesVerified,
                filteredNumberOfLeads=filtered_number_of_leads,
                filteredNumberOfLeadsInProgress=filtered_number_of_leadsInProgress,
                filteredNumberOfLeadsNotTagged=filtered_number_of_leadsNotTagged,
                filteredNumberOfLeadsTagged=filtered_number_of_leadsTagged,
            )

        # Without login
        _query_check(assert_for_error=True)

        # With login - non-member zero count
        self.force_login(non_member_user)
        content = _query_check()['data']['project']['stats']
        self.assertIsNone(content, content)

        # With login - member
        self.force_login(member_user)
        self.maxDiff = None
        for index, (filters, _expected) in enumerate([
                (
                    {'confidentiality': self.genum(Lead.Confidentiality.CONFIDENTIAL)},
                    [1, 1, 0, 0, 2, 2, 0]
                ),
                (
                    {'entriesFilterData': {'leadConfidentialities': self.genum(Lead.Confidentiality.CONFIDENTIAL)}},
                    [1, 1, 0, 0, 2, 2, 0]
                ),
                (
                    {'confidentiality': self.genum(Lead.Confidentiality.UNPROTECTED)},
                    [1, 0, 0, 1, 1, 0, 1]
                ),
                (
                    {'entriesFilterData': {'leadConfidentialities': self.genum(Lead.Confidentiality.UNPROTECTED)}},
                    [1, 0, 0, 1, 1, 0, 1]
                ),
        ]):
            content = _query_check(filters=filters)['data']['project']['stats']
            self.assertEqual(_expected_response(*_expected), content, index)

    def test_project_last_read_access(self):
        QUERY = '''
            query MyQuery ($projectId: ID!) {
              project(id: $projectId) {
                  id
                }
            }
        '''

        user = UserFactory.create()
        projects = ProjectFactory.create_batch(2)
        projects.extend(ProjectFactory.create_batch(2, is_private=True))

        project_with_access = [projects[0], projects[2]]

        for project in project_with_access:
            project.add_member(user, role=self.project_role_member)

        def _query_check(project_id):
            return self.query_check(QUERY, variables={'projectId': project_id})

        self.force_login(user)

        # Run/try query and check if last_read_access are changing properly
        base_now = datetime(2021, 1, 1, 0, 0, 0, 123456, tzinfo=pytz.UTC)
        with patch('deep.trackers.timezone.now') as timezone_now_mock:
            timezone_now = None
            old_timezone_now = None
            for timezone_now in [
                base_now,
                base_now + relativedelta(months=Project.PROJECT_INACTIVE_AFTER_MONTHS),
                base_now + 2 * relativedelta(months=Project.PROJECT_INACTIVE_AFTER_MONTHS),
            ]:
                # Current time
                timezone_now_mock.return_value = timezone_now
                for project in projects:
                    if project in project_with_access:
                        # Existing state
                        assert project.last_read_access == old_timezone_now
                    else:
                        # No access (no membership)
                        if project.is_private:
                            assert project.last_read_access is None
                        else:
                            # Public project have readaccess for some nodes
                            assert project.last_read_access == old_timezone_now
                    _query_check(project.id)['data']['project']
                    with self.captureOnCommitCallbacks(execute=True):
                        schedule_tracker_data_handler()
                    project.refresh_from_db()
                    if project in project_with_access:
                        # New state
                        assert project.last_read_access == timezone_now
                    else:
                        # No access (no membership)
                        if project.is_private:
                            assert project.last_read_access is None
                        else:
                            # Public project have readaccess for some nodes
                            assert project.last_read_access == timezone_now
                old_timezone_now = timezone_now

    def test_project_last_write_access(self):
        MUTATION = '''
            mutation MyMutation ($projectId: ID!) {
              project(id: $projectId) {
                  id
                }
            }
        '''

        user = UserFactory.create()
        projects = ProjectFactory.create_batch(2)
        projects.extend(
            ProjectFactory.create_batch(2, is_private=True)
        )

        project_with_access = [projects[0], projects[2]]

        for project in project_with_access:
            project.add_member(user, role=self.project_role_member)

        def _query_check(project_id, **kwargs):
            return self.query_check(MUTATION, variables={'projectId': project_id}, **kwargs)

        self.force_login(user)

        # Run/try mutations and check if last_write_access and project.status are changing properly
        base_now = datetime(2021, 1, 1, 0, 0, 0, 123456, tzinfo=pytz.UTC)
        with patch('deep.trackers.timezone.now') as timezone_now_mock:
            timezone_now = None
            old_timezone_now = None
            for timezone_now in [
                base_now,
                base_now + relativedelta(months=Project.PROJECT_INACTIVE_AFTER_MONTHS),
                base_now + 2 * relativedelta(months=Project.PROJECT_INACTIVE_AFTER_MONTHS),
            ]:
                # Current time
                timezone_now_mock.return_value = timezone_now
                for project in projects:
                    project.refresh_from_db()
                    if project in project_with_access:
                        # Existing state
                        assert project.last_write_access == old_timezone_now
                        _query_check(project.id)['data']['project']
                        with self.captureOnCommitCallbacks(execute=True):
                            schedule_tracker_data_handler()
                        project.refresh_from_db()
                        # New state
                        assert project.last_write_access == timezone_now
                        assert project.status == Project.Status.ACTIVE
                    else:
                        # None since we don't have access (no membership)
                        assert project.last_write_access is None
                        _query_check(project.id, assert_for_error=True)
                        with self.captureOnCommitCallbacks(execute=True):
                            schedule_tracker_data_handler()
                        project.refresh_from_db()
                        # Same we don't have access (no membership)
                        assert project.last_write_access is None
                        assert project.status == Project.Status.INACTIVE
                old_timezone_now = timezone_now

            # Without mutations, check if project.status is changing properly
            # After + 3*PROJECT_INACTIVE_AFTER_MONTHS
            # -- Check for auto status change
            assert timezone_now is not None
            timezone_now_mock.return_value = timezone_now + relativedelta(months=3 * Project.PROJECT_INACTIVE_AFTER_MONTHS)
            with self.captureOnCommitCallbacks(execute=True):
                schedule_tracker_data_handler()
            for project in projects:
                project.refresh_from_db()
                # It's inactive as ahead by Project.PROJECT_INACTIVE_AFTER_MONTHS
                assert project.status == Project.Status.INACTIVE

    def test_project_role(self):
        query = '''
            query MyQuery {
              projectRoles{
                id
                level
                title
                type

            }
        }
        '''
        user = UserFactory.create()

        # without login
        self.query_check(query, assert_for_error=True)
        # with login
        self.force_login(user)
        project_role_count = ProjectRole.objects.count()
        content = self.query_check(query)
        self.assertEqual(len(content['data']['projectRoles']), project_role_count)

    def test_user_pinned_projects_query(self):
        query = '''
            query MyQuery {
            userPinnedProjects {
                clientId
                id
                order
            }
        }
        '''

        user = UserFactory.create()
        non_member_user = UserFactory.create()
        project = ProjectFactory.create_batch(4)
        project_with_access = [project[0], project[2]]
        for idx, project in enumerate(project_with_access):
            project.add_member(user)
            ProjectPinnedFactory.create(
                project=project,
                user=user,
                order=idx
            )
        # -- Without login
        self.query_check(query, assert_for_error=True)

        # -- With login
        self.force_login(user)

        content = self.query_check(query)
        self.assertEqual(len(content['data']['userPinnedProjects']), 2)

        # -- With non member user
        self.force_login(non_member_user)
        content = self.query_check(query)
        self.assertEqual(len(content['data']['userPinnedProjects']), 0)


class TestProjectViz(GraphQLTestCase):
    ENABLE_NOW_PATCHER = True

    def test_projects_viz_node(self):
        query = '''
            query MyQuery ($id: ID!) {
              project(id: $id) {
                vizData {
                  dataUrl
                  modifiedAt
                  publicShare
                  publicUrl
                  status
                }
                title
                isVisualizationAvailable
                isVisualizationEnabled
              }
            }
        '''

        af = AnalysisFrameworkFactory.create()
        member_user = UserFactory.create()   # with confidential access
        non_confidential_user = UserFactory.create()
        non_member_user = UserFactory.create()
        project = ProjectFactory.create(analysis_framework=af)
        project.add_member(member_user, role=self.project_role_member)
        project.add_member(non_confidential_user, role=self.project_role_reader_non_confidential)

        def _query_check(**kwargs):
            return self.query_check(query, variables={'id': project.pk}, **kwargs)

        # -- Without login
        _query_check(assert_for_error=True)

        # -- With login
        # Before enabling viz.
        # --- non-member user
        self.force_login(non_member_user)
        content = _query_check()
        self.assertEqual(content['data']['project']['vizData'], None, content)
        self.assertEqual(content['data']['project']['isVisualizationEnabled'], False, content)
        self.assertEqual(content['data']['project']['isVisualizationAvailable'], False, content)

        # --- member user
        self.force_login(member_user)
        content = _query_check()
        self.assertEqual(content['data']['project']['vizData'], None, content)
        self.assertEqual(content['data']['project']['isVisualizationEnabled'], False, content)
        self.assertEqual(content['data']['project']['isVisualizationAvailable'], False, content)

        # Only enabling project viz settings (not configuring AF).
        project.is_visualization_enabled = True
        project.save(update_fields=('is_visualization_enabled',))
        # --- non-member user
        self.force_login(non_member_user)
        content = _query_check()
        self.assertEqual(content['data']['project']['vizData'], None, content)
        self.assertEqual(content['data']['project']['isVisualizationEnabled'], True, content)
        self.assertEqual(content['data']['project']['isVisualizationAvailable'], False, content)

        # --- member user
        self.force_login(member_user)
        content = _query_check()
        self.assertEqual(content['data']['project']['vizData'], None, content)
        self.assertEqual(content['data']['project']['isVisualizationEnabled'], True, content)
        self.assertEqual(content['data']['project']['isVisualizationAvailable'], False, content)

        # Configure/Enable viz.
        TestProjectGeneralMutationSnapshotTest.set_project_viz_configuration(project)

        # --- non-member project
        self.force_login(non_member_user)
        content = _query_check()
        self.assertEqual(content['data']['project']['vizData'], None, content)
        self.assertEqual(content['data']['project']['isVisualizationEnabled'], True, content)
        self.assertEqual(content['data']['project']['isVisualizationAvailable'], True, content)

        # --- member project
        self.force_login(member_user)
        content = _query_check()
        self.assertNotEqual(content['data']['project']['vizData'], None, content)
        self.assertEqual(content['data']['project']['isVisualizationEnabled'], True, content)
        self.assertEqual(content['data']['project']['isVisualizationAvailable'], True, content)
        self.assertEqual(
            content['data']['project']['vizData'],
            {
                'dataUrl': '',
                'modifiedAt': self.now_datetime_str(),
                'publicShare': False,
                'publicUrl': None,
                'status': self.genum(ProjectStats.Status.PENDING),
            },
            content,
        )

        # Enable public share/url
        project_stats = project.project_stats.update_public_share_configuration(ProjectStats.Action.ON)

        content = _query_check()
        self.assertNotEqual(content['data']['project']['vizData'], None, content)
        self.assertEqual(content['data']['project']['isVisualizationEnabled'], True, content)
        self.assertEqual(content['data']['project']['isVisualizationAvailable'], True, content)
        self.assertEqual(
            content['data']['project']['vizData'],
            {
                'dataUrl': '',
                'modifiedAt': self.now_datetime_str(),
                'publicShare': True,
                'publicUrl': 'http://testserver' + project_stats.get_public_url(),
                'status': self.genum(ProjectStats.Status.PENDING),
            },
            content,
        )


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

    def test_query_test_projects_filter(self):
        query = '''
            query MyQuery ($isTest: Boolean!) {
              projects(isTest: $isTest) {
                page
                pageSize
                totalCount
                results {
                  id
                  title
                  isTest
                  currentUserRole
                }
              }
            }
        '''

        user = UserFactory.create()
        project1, project2 = ProjectFactory.create_batch(2, is_test=True)
        project3 = ProjectFactory.create()

        # -- Without login
        self.query_check(query, variables={'isTest': True}, assert_for_error=True)

        # -- With login
        self.force_login(user)

        # test projects
        content = self.query_check(query, variables={'isTest': True})
        self.assertEqual(content['data']['projects']['totalCount'], 2, content)
        self.assertListIds(content['data']['projects']['results'], [project1, project2], content)
        # except test projects
        content = self.query_check(query, variables={'isTest': False})
        self.assertEqual(content['data']['projects']['totalCount'], 1, content)
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


class TestProjectExploreStats(GraphQLSnapShotTestCase):
    factories_used = [ProjectFactory, AnalysisFrameworkFactory]

    def test_snapshot(self):
        query = '''
            query MyQuery {
              projectExploreStats {
                totalProjects
                totalUsers
                totalLeads
                totalEntries
                leadsAddedWeekly
                dailyAverageLeadsTaggedPerProject
                generatedExportsMonthly
                topActiveProjects {
                  projectId
                  projectTitle
                  analysisFrameworkId
                  analysisFrameworkTitle
                }
                calculatedAt
              }
            }
        '''

        def _cache_clear():
            cache.delete(CacheKey.PROJECT_EXPLORE_STATS_LOADER_KEY)  # Delete cache

        user = UserFactory.create()

        # -- With login
        self.force_login(user)

        _cache_clear()

        previous_content = content = self.query_check(query)
        self.assertMatchSnapshot(content, 'no-data')

        UserFactory.create_batch(3, is_active=False)  # Some Inactive users
        analysis_framework = AnalysisFrameworkFactory.create()
        projects = ProjectFactory.create_batch(3)
        projects_with_af = ProjectFactory.create_batch(3, analysis_framework=analysis_framework)
        # This shouldn't show in top projects but leads/entries count should
        private_project = ProjectFactory.create(
            title='Private Project', is_private=True, analysis_framework=analysis_framework)
        now = timezone.now()

        # Generate project cache
        _generate_project_stats_cache()

        content = self.query_check(query)
        self.assertEqual(content, previous_content)  # Test for cache
        _cache_clear()
        previous_content = content = self.query_check(query)  # Pull latest data
        self.assertMatchSnapshot(content, 'only-project')

        self.update_obj(LeadFactory.create(project=projects[0]), created_at=now + relativedelta(weeks=-1))
        self.update_obj(LeadFactory.create(project=projects[0]), created_at=now + relativedelta(weeks=-1))
        self.update_obj(LeadFactory.create(project=projects[1]), created_at=now + relativedelta(weeks=-2))
        self.update_obj(LeadFactory.create(project=projects[1]), created_at=now + relativedelta(weeks=-1))
        self.update_obj(LeadFactory.create(project=projects[1]), created_at=now + relativedelta(weeks=-1))
        self.update_obj(LeadFactory.create(project=projects[2]), created_at=now + relativedelta(weeks=-2))

        lead0_1 = self.update_obj(LeadFactory.create(project=projects_with_af[0]), created_at=now + relativedelta(weeks=-1))
        lead1_1 = self.update_obj(LeadFactory.create(project=projects_with_af[1]), created_at=now + relativedelta(weeks=-2))
        lead1_2 = self.update_obj(LeadFactory.create(project=projects_with_af[1]), created_at=now + relativedelta(weeks=-1))
        plead1_1 = self.update_obj(LeadFactory.create(project=private_project), created_at=now + relativedelta(weeks=-2))
        plead1_2 = self.update_obj(LeadFactory.create(project=private_project), created_at=now + relativedelta(weeks=-1))
        self.update_obj(LeadFactory.create(project=projects_with_af[1]), created_at=now + relativedelta(weeks=-1))
        self.update_obj(LeadFactory.create(project=projects_with_af[2]), created_at=now + relativedelta(weeks=-3))

        self.update_obj(EntryFactory.create(lead=lead0_1), created_at=now + relativedelta(weeks=-1))
        self.update_obj(EntryFactory.create(lead=lead1_1), created_at=now + relativedelta(weeks=-1))
        self.update_obj(EntryFactory.create(lead=lead1_2), created_at=now + relativedelta(weeks=-1))
        self.update_obj(EntryFactory.create(lead=plead1_1), created_at=now + relativedelta(weeks=-1))
        self.update_obj(EntryFactory.create(lead=plead1_2), created_at=now + relativedelta(weeks=-1))

        # Generate project cache
        _generate_project_stats_cache()

        self.update_obj(
            ExportFactory.create(project=projects_with_af[0], exported_by=user), exported_at=now + relativedelta(months=-1))
        self.update_obj(
            ExportFactory.create(project=projects_with_af[0], exported_by=user), exported_at=now + relativedelta(months=-1))
        self.update_obj(
            ExportFactory.create(project=projects_with_af[0], exported_by=user), exported_at=now + relativedelta(months=-2))
        self.update_obj(
            ExportFactory.create(project=projects_with_af[1], exported_by=user), exported_at=now + relativedelta(months=-2))
        self.update_obj(
            ExportFactory.create(project=projects_with_af[2], exported_by=user), exported_at=now + relativedelta(months=-3))
        self.update_obj(
            ExportFactory.create(project=private_project, exported_by=user), exported_at=now + relativedelta(months=-1))

        content = self.query_check(query)
        self.assertEqual(content, previous_content)  # Test for cache
        _cache_clear()
        previous_content = content = self.query_check(query)  # Pull latest data
        self.assertMatchSnapshot(content, 'with-data')
