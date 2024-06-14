from datetime import timedelta
from unittest import mock

from analysis_framework.factories import AnalysisFrameworkFactory, WidgetFactory
from entry.factories import EntryAttributeFactory, EntryFactory
from factory import fuzzy
from geo.factories import RegionFactory
from lead.factories import LeadFactory
from notification.models import Notification
from organization.factories import OrganizationFactory
from project.factories import (
    ProjectFactory,
    ProjectJoinRequestFactory,
    ProjectOrganizationFactory,
    ProjectPinnedFactory,
)
from project.models import (
    Project,
    ProjectChangeLog,
    ProjectJoinRequest,
    ProjectMembership,
    ProjectOrganization,
    ProjectRole,
    ProjectStats,
    ProjectUserGroupMembership,
    get_default_role_id,
)
from project.tasks import _generate_project_viz_stats, permanently_delete_projects
from user.factories import FeatureFactory, UserFactory
from user.models import Feature
from user.utils import (
    send_project_accept_email,
    send_project_join_request_emails,
    send_project_reject_email,
)
from user_group.factories import UserGroupFactory

from utils.graphene.tests import GraphQLSnapShotTestCase, GraphQLTestCase

from . import entry_stats_data


class TestProjectGeneralMutationSnapshotTest(GraphQLSnapShotTestCase):
    ENABLE_NOW_PATCHER = True

    @staticmethod
    def set_project_viz_configuration(project):
        w_data = entry_stats_data.WIDGET_DATA
        a_data = entry_stats_data.ATTRIBUTE_DATA

        lead = LeadFactory.create(project=project)
        entry = EntryFactory.create(lead=lead)
        af = project.analysis_framework

        # Create widgets, attributes and configs
        invalid_stat_config = {}
        valid_stat_config = {}

        for index, (title, widget_identifier, data_identifier, config_kwargs) in enumerate(
            [
                ("widget 1d", "widget_1d", "matrix1dWidget", {}),
                ("widget 2d", "widget_2d", "matrix2dWidget", {}),
                ("geo widget", "geo_widget", "geoWidget", {}),
                ("reliability widget", "reliability_widget", "scaleWidget", {}),
                ("affected groups widget", "affected_groups_widget", "multiselectWidget", {}),
                ("specific needs groups widget", "specific_needs_groups_widget", "multiselectWidget", {}),
            ]
        ):
            widget = WidgetFactory.create(
                analysis_framework=af,
                section=None,
                title=title,
                widget_id=data_identifier,
                key=f"{data_identifier}-{index}",
                properties={"data": w_data[data_identifier]},
            )
            EntryAttributeFactory.create(entry=entry, widget=widget, data=a_data[data_identifier])
            valid_stat_config[widget_identifier] = {
                "pk": widget.pk,
                **config_kwargs,
            }
            invalid_stat_config[widget_identifier] = {"pk": 0}

        af.properties = {"stats_config": invalid_stat_config}
        af.save(update_fields=("properties",))

        project.is_visualization_enabled = True
        project.save(update_fields=("is_visualization_enabled",))

    def test_projects_viz_configuration_update(self):
        query = """
            mutation MyMutation($id: ID!, $input: ProjectVizConfigurationInputType!) {
              project(id: $id) {
                projectVizConfigurationUpdate(data: $input) {
                  ok
                  errors
                  result {
                    dataUrl
                    modifiedAt
                    publicShare
                    publicUrl
                    status
                  }
                }
              }
            }
        """

        normal_user = UserFactory.create()
        admin_user = UserFactory.create()
        member_user = UserFactory.create()
        af = AnalysisFrameworkFactory.create()
        project = ProjectFactory.create(analysis_framework=af)

        self.set_project_viz_configuration(project)
        project.add_member(admin_user, role=self.project_role_admin)
        project.add_member(member_user, role=self.project_role_member)

        minput = dict(action=None)

        def _query_check(**kwargs):
            return self.query_check(
                query,
                minput=minput,
                mnested=["project"],
                variables={"id": project.id},
                **kwargs,
            )

        Action = ProjectStats.Action
        _generate_project_viz_stats(project.pk)
        # Check permission for token generation
        for action in [Action.NEW, Action.OFF, Action.NEW, Action.ON]:
            for user, assertLogic in [
                (normal_user, self.assert_403),
                (member_user, self.assert_403),
                (admin_user, self.assert_200),
            ]:
                self.force_login(user)
                current_stats = project.project_stats
                minput["action"] = self.genum(action)
                if assertLogic == self.assert_200:
                    content = _query_check(okay=True)
                else:
                    _query_check(assert_for_error=True)
                    continue
                response = content["data"]["project"]["projectVizConfigurationUpdate"]["result"]
                if assertLogic == self.assert_200:
                    if action == "new":
                        assert response["publicUrl"] != current_stats.token
                        # Logout and check if response is okay
                        self.client.logout()
                        rest_response = self.client.get(f"{response['publicUrl']}?format=json")
                        self.assert_200(rest_response)
                    elif action == "on":
                        assert (response["publicUrl"] is not None) or (response["publicUrl"] == current_stats.token)
                        # Logout and check if response is not okay
                        self.client.logout()
                        rest_response = self.client.get(f"{response['publicUrl']}?format=json")
                        self.assert_200(rest_response)
                    elif action == "off":
                        assert (response["publicUrl"] is not None) or (response["publicUrl"] == current_stats.token)
                        # Logout and check if response is not okay
                        self.client.logout()
                        rest_response = self.client.get(f"{response['publicUrl']}?format=json")
                        self.assert_403(rest_response)
        # Check Project change logs
        self.assertMatchSnapshot(
            list(ProjectChangeLog.objects.filter(project=project).order_by("id").values("action", "diff")),
            "project-change-log",
        )


class ProjectMutationSnapshotTest(GraphQLSnapShotTestCase):
    factories_used = [
        UserFactory,
        ProjectFactory,
        AnalysisFrameworkFactory,
        OrganizationFactory,
        RegionFactory,
    ]

    def test_project_create_mutation(self):
        query = """
            mutation MyMutation($input: ProjectCreateInputType!) {
              __typename
              projectCreate(data: $input) {
                ok
                errors
                result {
                  id
                  title
                  analysisFramework {
                    id
                    isPrivate
                  }
                  description
                  startDate
                  endDate
                  isPrivate
                  hasPubliclyViewableUnprotectedLeads
                  hasPubliclyViewableRestrictedLeads
                  hasPubliclyViewableConfidentialLeads
                  isVisualizationEnabled
                  organizations {
                    id
                    organization {
                      id
                      title
                    }
                    organizationType
                    organizationTypeDisplay
                  }
                  status
                }
              }
            }
        """

        user = UserFactory.create()
        af = AnalysisFrameworkFactory.create()
        private_project_feature = FeatureFactory.create(key=Feature.FeatureKey.PRIVATE_PROJECT)
        private_af = AnalysisFrameworkFactory.create(is_private=True)
        private_af_w_membership = AnalysisFrameworkFactory.create(is_private=True)
        private_af_w_membership.add_member(user)

        org1 = OrganizationFactory.create()

        minput = dict(
            title="Project 1",
            analysisFramework=str(private_af.id),
            description="Project description 101",
            startDate="2020-01-01",
            endDate="2021-01-01",
            status=self.genum(Project.Status.ACTIVE),
            isPrivate=True,
            hasPubliclyViewableUnprotectedLeads=False,
            hasPubliclyViewableRestrictedLeads=False,
            hasPubliclyViewableConfidentialLeads=False,
            isVisualizationEnabled=False,
            organizations=[
                dict(
                    organization=str(org1.pk),
                    organizationType=self.genum(ProjectOrganization.Type.LEAD_ORGANIZATION),
                ),
            ],
        )

        def _query_check(**kwargs):
            response = self.query_check(
                query,
                minput=minput,
                **kwargs,
            )
            if kwargs.get("okay"):
                project_log = ProjectChangeLog.objects.get(project=response["data"]["projectCreate"]["result"]["id"])
                assert project_log.action == ProjectChangeLog.Action.PROJECT_CREATE
            return response

        # ---------- Without login
        _query_check(assert_for_error=True)
        # ---------- With login
        self.force_login(user)
        # ----------------- Some Invalid input
        response = _query_check(okay=False)

        # invalid [private AF with memership] + public project
        minput["analysisFramework"] = str(private_af_w_membership.pk)
        minput["isPrivate"] = False
        response = _query_check(okay=False)
        # invalid [private AF with memership] + private project + without feature permission
        minput["isPrivate"] = True
        response = _query_check(okay=False)
        # invalid [private AF with memership] + private project + with feature permission
        private_project_feature.users.add(user)
        response = _query_check(okay=True)["data"]["projectCreate"]
        self.assertMatchSnapshot(response, "private-af-private-project-success")
        # Valid [public AF] + private project
        minput["title"] = "Project 2"
        minput["analysisFramework"] = str(af.pk)
        minput["isPrivate"] = True
        response = _query_check(okay=True)["data"]["projectCreate"]
        self.assertMatchSnapshot(response, "public-af-private-project-success")

        # Valid [public AF] + private project
        minput["title"] = "Project 3"
        minput["analysisFramework"] = str(af.pk)
        minput["isPrivate"] = False
        response = _query_check(okay=True)["data"]["projectCreate"]
        self.assertMatchSnapshot(response, "public-af-public-project-success")

        minput["title"] = "Project 1"
        response = _query_check(okay=False)

    def test_project_update_mutation(self):
        query = """
            mutation MyMutation($projectId: ID!, $input: ProjectUpdateInputType!) {
              __typename
              project(id: $projectId) {
                  projectUpdate(data: $input) {
                    ok
                    errors
                    result {
                      id
                      title
                      analysisFramework {
                        id
                        isPrivate
                      }
                      description
                      startDate
                      endDate
                      isPrivate
                      hasPubliclyViewableUnprotectedLeads
                      hasPubliclyViewableRestrictedLeads
                      hasPubliclyViewableConfidentialLeads
                      isVisualizationEnabled
                      organizations {
                        id
                        organization {
                          id
                          title
                        }
                        organizationType
                        organizationTypeDisplay
                      }
                      status
                    }
                  }
              }
            }
        """

        user = UserFactory.create()
        normal_user = UserFactory.create()
        another_user = UserFactory.create()
        af = AnalysisFrameworkFactory.create()

        org1, org2, org3 = OrganizationFactory.create_batch(3)

        private_af = AnalysisFrameworkFactory.create(is_private=True)
        private_af_2 = AnalysisFrameworkFactory.create(is_private=True)

        private_af_w_membership = AnalysisFrameworkFactory.create(is_private=True)
        private_af_w_membership.add_member(user)

        public_project = ProjectFactory.create(
            title="Public Project 101",
            analysis_framework=af,
        )
        private_project = ProjectFactory.create(
            title="Private Project 101",
            analysis_framework=private_af,
            is_private=True,
        )

        ProjectOrganizationFactory.create(
            project=public_project,
            organization=org2,
            organization_type=ProjectOrganization.Type.DONOR,
        )
        ProjectOrganizationFactory.create(
            project=public_project,
            organization=org1,
            organization_type=ProjectOrganization.Type.GOVERNMENT,
        )
        ProjectOrganizationFactory.create(
            project=private_project,
            organization=org2,
            organization_type=ProjectOrganization.Type.NATIONAL_PARTNER,
        )

        public_project.add_member(user, role=self.project_role_owner)
        private_project.add_member(user, role=self.project_role_owner)
        public_project.add_member(normal_user)

        public_minput = dict(
            title=f"{public_project.title} (Updated)",
            analysisFramework=str(public_project.analysis_framework.id),
            isTest=True,
            isPrivate=False,
            hasPubliclyViewableUnprotectedLeads=True,
            hasPubliclyViewableRestrictedLeads=True,
            hasPubliclyViewableConfidentialLeads=True,
            organizations=[
                dict(
                    organization=str(org1.pk),
                    organizationType=self.genum(ProjectOrganization.Type.LEAD_ORGANIZATION),
                ),
            ],
        )

        private_minput = dict(
            title=private_project.title,
            description="Added some description",
            analysisFramework=str(private_project.analysis_framework.id),
            isPrivate=True,
            organizations=[
                dict(
                    organization=str(org1.pk),
                    organizationType=self.genum(ProjectOrganization.Type.LEAD_ORGANIZATION),
                ),
            ],
        )

        def _query_check(project, minput, **kwargs):
            return self.query_check(
                query,
                minput=minput,
                mnested=["project"],
                variables={"projectId": str(project.pk)},
                **kwargs,
            )

        def _public_query_check(**kwargs):
            return _query_check(public_project, public_minput, **kwargs)

        def _private_query_check(**kwargs):
            return _query_check(private_project, private_minput, **kwargs)

        # ---------- Without login
        _public_query_check(assert_for_error=True)
        _private_query_check(assert_for_error=True)
        # ---------- With login (non member)
        self.force_login(another_user)
        _public_query_check(assert_for_error=True)
        _private_query_check(assert_for_error=True)
        # ---------- With login (member with low access)
        self.force_login(normal_user)
        _public_query_check(assert_for_error=True)
        _private_query_check(assert_for_error=True)

        # ---------- With login (member with high access)
        self.force_login(user)
        _public_query_check(okay=True)
        _private_query_check(okay=True)

        # WITH ACCESS
        # ----- isPrivate attribute
        # [changing private status) [public project]
        public_minput["isPrivate"] = True
        self.assertMatchSnapshot(_public_query_check(okay=False), "public-project:is-private-change-error")
        public_minput["isPrivate"] = False

        # [changing private status) [public project]
        private_minput["isPrivate"] = False
        self.assertMatchSnapshot(_private_query_check(okay=False), "private-project:is-private-change-error")
        private_minput["isPrivate"] = True

        # ----- AF attribute
        # [changing private status) [public project]
        public_minput["analysisFramework"] = str(private_af.id)
        self.assertMatchSnapshot(_public_query_check(okay=False), "public-project:private-af")
        public_minput["analysisFramework"] = str(private_af_w_membership.id)
        self.assertMatchSnapshot(_public_query_check(okay=False), "public-project:private-af-with-membership")
        public_minput["analysisFramework"] = str(public_project.analysis_framework_id)

        # [changing private status) [private project]
        private_minput["analysisFramework"] = str(private_af_2.id)
        self.assertMatchSnapshot(_private_query_check(okay=False), "private-project:private-af")
        private_minput["analysisFramework"] = str(private_af_w_membership.id)
        _private_query_check(okay=True)
        private_minput["analysisFramework"] = str(private_project.analysis_framework_id)
        # Check Project change logs
        project_log = ProjectChangeLog.objects.get(project=public_project)
        assert project_log.action == ProjectChangeLog.Action.MULTIPLE
        self.assertMatchSnapshot(project_log.diff, "public-project:project-change:diff")
        project_logs = list(ProjectChangeLog.objects.filter(project=private_project).order_by("id"))
        assert project_logs[0].action == ProjectChangeLog.Action.MULTIPLE
        self.assertMatchSnapshot(project_logs[0].diff, "private-project-0:project-change:diff")
        assert project_logs[1].action == ProjectChangeLog.Action.FRAMEWORK
        self.assertMatchSnapshot(project_logs[1].diff, "private-project-1:project-change:diff")

    def test_project_region_action_mutation(self):
        query = """
            mutation MyMutation ($projectId: ID!, $regionsToAdd: [ID!], $regionsToRemove: [ID!]) {
              project(id: $projectId) {
                projectRegionBulk(regionsToAdd: $regionsToAdd, regionsToRemove: $regionsToRemove) {
                  result {
                    id
                    title
                  }
                  deletedResult {
                    id
                    title
                  }
                }
              }
            }
        """

        user = UserFactory.create()
        normal_user = UserFactory.create()
        another_user = UserFactory.create()
        af = AnalysisFrameworkFactory.create()
        project = ProjectFactory.create(title="Project 101", analysis_framework=af)
        project.add_member(user, role=self.project_role_owner)
        project.add_member(normal_user)
        region_public_zero = RegionFactory.create(title="public-region-zero")
        region_public = RegionFactory.create(title="public-region")
        region_private = RegionFactory.create(title="private-region", public=False)
        region_private_owner = RegionFactory.create(title="private-region-owner", public=False, created_by=user)
        # Region with project membership
        # -- Normal
        region_private_with_membership = RegionFactory.create(title="private-region-with-membership", public=False)
        another_project_for_membership = ProjectFactory.create()
        another_project_for_membership.regions.add(region_private_with_membership)
        another_project_for_membership.add_member(user, role=self.project_role_admin)
        # -- Admin
        region_private_with_membership_admin = RegionFactory.create(title="private-region-with-membership", public=False)
        another_project_for_membership_admin = ProjectFactory.create()
        another_project_for_membership_admin.regions.add(region_private_with_membership_admin)
        another_project_for_membership_admin.add_member(user, role=self.project_role_admin)

        project.regions.add(region_public_zero)

        def _query_check(add, remove, **kwargs):
            return self.query_check(
                query,
                mnested=["project"],
                variables={
                    "projectId": str(project.pk),
                    "regionsToAdd": add,
                    "regionsToRemove": remove,
                },
                **kwargs,
            )

        # ---------- Without login
        _query_check([], [], assert_for_error=True)
        # ---------- With login (non member)
        self.force_login(another_user)
        _query_check([], [], assert_for_error=True)
        # ---------- With login (member + low access)
        self.force_login(normal_user)
        _query_check([], [], assert_for_error=True)
        # ---------- With login (member with high access)
        self.force_login(user)
        # Simple checkup
        response = _query_check([], [])
        self.assertEqual(
            response["data"]["project"]["projectRegionBulk"],
            {
                "deletedResult": [],
                "result": [],
            },
        )

        # Add
        response = _query_check(
            [
                str(region_public.pk),
                str(region_private.pk),
                str(region_private_owner.pk),
                str(region_private_with_membership.pk),
            ],
            [
                str(region_public_zero.pk),
            ],
        )
        self.assertEqual(
            response["data"]["project"]["projectRegionBulk"],
            {
                "deletedResult": [
                    dict(id=str(region_public_zero.pk), title=region_public_zero.title),
                ],
                "result": [
                    dict(id=str(region_public.pk), title=region_public.title),
                    dict(id=str(region_private_owner.pk), title=region_private_owner.title),
                    dict(id=str(region_private_with_membership.pk), title=region_private_with_membership.title),
                ],
            },
        )
        self.assertEqual(
            list(project.regions.values_list("id", flat=True).order_by("id")),
            [
                region_public.pk,
                region_private_owner.pk,
                region_private_with_membership.pk,
            ],
        )

        # Delete
        response = _query_check(
            [],
            [
                str(region_public.pk),
                str(region_private.pk),
                str(region_private_owner.pk),
                str(region_private_with_membership.pk),
            ],
        )
        self.assertEqual(
            response["data"]["project"]["projectRegionBulk"],
            {
                "deletedResult": [
                    dict(id=str(region_public.pk), title=region_public.title),
                    dict(id=str(region_private_owner.pk), title=region_private_owner.title),
                    dict(id=str(region_private_with_membership.pk), title=region_private_with_membership.title),
                ],
                "result": [],
            },
        )
        self.assertEqual(list(project.regions.values_list("id", flat=True).order_by("id")), [])
        # Check Project change logs
        self.assertMatchSnapshot(
            list(ProjectChangeLog.objects.filter(project=project).order_by("id").values("action", "diff")),
            "project-change-log",
        )


class TestProjectJoinMutation(GraphQLTestCase):
    def setUp(self):
        self.project_join_mutation = """
            mutation Mutation($input: ProjectJoinRequestInputType!) {
              joinProject(data: $input) {
                ok
                errors
                result {
                  id
                  data
                  project {
                    id
                  }
                  status
                  requestedBy {
                    id
                  }
                }
              }
            }
        """
        super().setUp()

    @mock.patch("project.serializers.send_project_join_request_emails.delay", side_effect=send_project_join_request_emails.delay)
    def test_valid_project_join(self, send_project_join_request_email_mock):
        user = UserFactory.create()
        admin_user = UserFactory.create()
        project = ProjectFactory.create()
        project.add_member(admin_user, role=ProjectRole.get_admin_role())
        reason = fuzzy.FuzzyText(length=100).fuzz()
        minput = dict(project=project.id, reason=reason)
        self.force_login(user)
        notification_qs = Notification.objects.filter(
            receiver=admin_user, project=project, notification_type=Notification.Type.PROJECT_JOIN_REQUEST
        )
        old_count = notification_qs.count()
        with self.captureOnCommitCallbacks(execute=True):
            content = self.query_check(self.project_join_mutation, minput=minput, okay=True)
        self.assertEqual(content["data"]["joinProject"]["result"]["requestedBy"]["id"], str(user.id), content)
        self.assertEqual(content["data"]["joinProject"]["result"]["project"]["id"], str(project.id), content)
        send_project_join_request_email_mock.assert_called_once()
        # confirm that the notification is also created
        assert notification_qs.count() > old_count

    def test_already_member_project(self):
        user = UserFactory.create()
        project = ProjectFactory.create()
        project.add_member(user)
        reason = fuzzy.FuzzyText(length=100).fuzz()
        minput = dict(project=project.id, reason=reason)
        self.force_login(user)
        content = self.query_check(self.project_join_mutation, minput=minput, okay=False)
        self.assertEqual(len(content["data"]["joinProject"]["errors"]), 1, content)

    def test_project_join_reason_length(self):
        user = UserFactory.create()
        project1, project2 = ProjectFactory.create_batch(2)
        reason = fuzzy.FuzzyText(length=49).fuzz()
        minput = dict(project=project1.id, reason=reason)
        self.force_login(user)
        # Invalid
        content = self.query_check(self.project_join_mutation, minput=minput, okay=False)
        self.assertEqual(len(content["data"]["joinProject"]["errors"]), 1, content)
        # Invalid
        minput["reason"] = fuzzy.FuzzyText(length=501).fuzz()
        content = self.query_check(self.project_join_mutation, minput=minput, okay=False)
        self.assertEqual(len(content["data"]["joinProject"]["errors"]), 1, content)
        # Valid (Project 1) max=500
        minput["reason"] = fuzzy.FuzzyText(length=500).fuzz()
        content = self.query_check(self.project_join_mutation, minput=minput, okay=True)
        self.assertEqual(content["data"]["joinProject"]["errors"], None, content)
        # Valid (Project 2) min=50
        minput["reason"] = fuzzy.FuzzyText(length=50).fuzz()
        minput["project"] = project2.pk
        content = self.query_check(self.project_join_mutation, minput=minput, okay=True)
        self.assertEqual(content["data"]["joinProject"]["errors"], None, content)

    def test_join_private_project(self):
        user = UserFactory.create()
        project = ProjectFactory.create(is_private=True)
        reason = fuzzy.FuzzyText(length=50).fuzz()
        minput = dict(project=project.id, reason=reason)
        self.force_login(user)
        content = self.query_check(self.project_join_mutation, minput=minput, okay=False)
        self.assertEqual(len(content["data"]["joinProject"]["errors"]), 1, content)

    def test_already_request_sent_for_project(self):
        user = UserFactory.create()
        project = ProjectFactory.create()
        # lets create a join request for the project
        ProjectJoinRequestFactory.create(
            requested_by=user,
            project=project,
            role=ProjectRole.get_default_role(),
            status=ProjectJoinRequest.Status.PENDING,
        )
        reason = fuzzy.FuzzyText(length=50).fuzz()
        minput = dict(project=project.id, reason=reason)
        self.force_login(user)
        content = self.query_check(self.project_join_mutation, minput=minput, okay=False)
        self.assertEqual(len(content["data"]["joinProject"]["errors"]), 1, content)


class TestProjectJoinDeleteMutation(GraphQLTestCase):
    def setUp(self):
        self.project_join_request_delete_mutation = """
            mutation Mutation($projectId: ID!) {
              projectJoinRequestDelete(projectId: $projectId) {
                ok
                errors
                result {
                  data
                  project {
                    id
                  }
                  status
                  requestedBy {
                    id
                  }
                }
              }
            }
        """
        super().setUp()

    def test_delete_project_join_request(self):
        user = UserFactory.create()
        project = ProjectFactory.create()
        ProjectJoinRequestFactory.create(
            requested_by=user,
            project=project,
            role=ProjectRole.get_default_role(),
            status=ProjectJoinRequest.Status.PENDING,
        )
        join_request_qs = ProjectJoinRequest.objects.filter(requested_by=user, project=project)
        old_join_request_count = join_request_qs.count()

        self.force_login(user)
        self.query_check(self.project_join_request_delete_mutation, variables={"projectId": project.id}, okay=True)
        self.assertEqual(join_request_qs.count(), old_join_request_count - 1)


class TestProjectJoinAcceptRejectMutation(GraphQLSnapShotTestCase):
    def setUp(self):
        self.projet_accept_reject_mutation = """
            mutation MyMutation ($projectId: ID! $joinRequestId: ID! $input: ProjectAcceptRejectInputType!) {
              project(id: $projectId) {
                acceptRejectProject(id: $joinRequestId, data: $input) {
                  ok
                  errors
                  result {
                    data
                    project {
                      id
                    }
                    status
                    requestedBy {
                      id
                    }
                    respondedBy {
                      id
                    }
                  }
                }
              }
            }
        """
        super().setUp()

    @mock.patch("project.serializers.send_project_accept_email.delay", side_effect=send_project_accept_email.delay)
    def test_project_join_request_accept(self, send_project_accept_email_mock):
        user = UserFactory.create()
        user2 = UserFactory.create()
        project = ProjectFactory.create()
        project.add_member(user, role=self.project_role_admin)
        join_request = ProjectJoinRequestFactory.create(
            requested_by=user2, project=project, role=ProjectRole.get_default_role(), status=ProjectJoinRequest.Status.PENDING
        )
        minput = dict(status=self.genum(ProjectJoinRequest.Status.ACCEPTED), role="normal")

        # without login
        self.query_check(
            self.projet_accept_reject_mutation,
            minput=minput,
            variables={"projectId": project.id, "joinRequestId": join_request.id},
            assert_for_error=True,
        )
        notification_qs = Notification.objects.filter(receiver=user, notification_type=Notification.Type.PROJECT_JOIN_RESPONSE)
        old_count = notification_qs.count()

        # with login
        self.force_login(user)
        with self.captureOnCommitCallbacks(execute=True):
            content = self.query_check(
                self.projet_accept_reject_mutation,
                minput=minput,
                variables={"projectId": project.id, "joinRequestId": join_request.id},
            )
        self.assertEqual(content["data"]["project"]["acceptRejectProject"]["result"]["requestedBy"]["id"], str(user2.id), content)
        self.assertEqual(content["data"]["project"]["acceptRejectProject"]["result"]["respondedBy"]["id"], str(user.id), content)
        self.assertEqual(
            content["data"]["project"]["acceptRejectProject"]["result"]["status"],
            self.genum(ProjectJoinRequest.Status.ACCEPTED),
            content,
        )
        # make sure memberships is created
        self.assertIn(user2.id, ProjectMembership.objects.filter(project=project).values_list("member", flat=True))
        assert notification_qs.count() > old_count
        send_project_accept_email_mock.assert_called_once()
        # Check Project change logs
        self.assertMatchSnapshot(
            list(ProjectChangeLog.objects.filter(project=project).order_by("id").values("action", "diff")),
            "project-change-log",
        )

    @mock.patch("project.serializers.send_project_reject_email.delay", side_effect=send_project_reject_email.delay)
    def test_project_join_request_reject(self, send_project_reject_email_mock):
        user = UserFactory.create()
        user2 = UserFactory.create()
        project = ProjectFactory.create()
        project.add_member(user, role=self.project_role_admin)
        join_request = ProjectJoinRequestFactory.create(
            requested_by=user2, project=project, role=ProjectRole.get_default_role(), status=ProjectJoinRequest.Status.PENDING
        )
        minput = dict(status=self.genum(ProjectJoinRequest.Status.REJECTED))
        # without login
        self.query_check(
            self.projet_accept_reject_mutation,
            minput=minput,
            variables={"projectId": project.id, "joinRequestId": join_request.id},
            assert_for_error=True,
        )

        # with login
        self.force_login(user)
        with self.captureOnCommitCallbacks(execute=True):
            content = self.query_check(
                self.projet_accept_reject_mutation,
                minput=minput,
                variables={"projectId": project.id, "joinRequestId": join_request.id},
            )
        self.assertEqual(
            content["data"]["project"]["acceptRejectProject"]["result"]["status"],
            self.genum(ProjectJoinRequest.Status.REJECTED),
            content,
        )
        send_project_reject_email_mock.assert_called_once()
        # Check project change logs
        assert ProjectChangeLog.objects.filter(project=project).count() == 0


class TestProjectMembershipMutation(GraphQLSnapShotTestCase):
    ENABLE_NOW_PATCHER = True

    def _user_membership_bulk(self, user_role):
        query = """
          mutation MyMutation(
              $id: ID!,
              $projectMembership: [BulkProjectMembershipInputType!],
              $projectMembershipDelete: [ID!]!
          ) {
          project(id: $id) {
            id
            title
            projectUserMembershipBulk(items: $projectMembership, deleteIds: $projectMembershipDelete) {
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
                badges
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
                  level
                }
                addedBy {
                  id
                  displayName
                }
                badges
              }
            }
          }
        }
        """
        creater_user = UserFactory.create()
        user = UserFactory.create()
        low_permission_user = UserFactory.create()
        non_member_user = UserFactory.create()

        (
            member_user0,
            member_user1,
            member_user2,
            member_user3,
            member_user4,
            member_user5,
            member_user6,
            member_user7,
        ) = UserFactory.create_batch(8)

        project = ProjectFactory.create(created_by=creater_user)
        user_group = UserGroupFactory.create(title="Group-1")
        membership1 = project.add_member(member_user1, badges=[ProjectMembership.BadgeType.QA])
        membership2 = project.add_member(member_user2)
        membership_using_user_group = project.add_member(member_user7, linked_group=user_group)
        project.add_member(member_user5)
        creater_user_membership = project.add_member(creater_user, role=self.project_role_owner)
        another_clairvoyant_user = project.add_member(member_user0, role=self.project_role_owner)
        user_membership = project.add_member(user, role=user_role)
        project.add_member(low_permission_user)

        minput = dict(
            projectMembershipDelete=[
                str(membership1.pk),  # This will be only on try 1
                # This shouldn't be on any response (requester + creater)
                str(user_membership.pk),
                str(creater_user_membership.pk),
                str(another_clairvoyant_user.pk),
            ],
            projectMembership=[
                # Try updating membership (Valid on try 1, invalid on try 2)
                dict(
                    member=member_user2.pk,
                    clientId="member-user-2",
                    role=self.project_role_owner.pk,
                    id=membership2.pk,
                    badges=[self.genum(ProjectMembership.BadgeType.QA)],
                ),
                # Try adding already existing member
                dict(
                    member=member_user5.pk,
                    clientId="member-user-5",
                    role=self.project_role_member.pk,
                ),
                # Try adding new member (Valid on try 1, invalid on try 2)
                dict(
                    member=member_user3.pk,
                    clientId="member-user-3",
                    role=self.project_role_member.pk,
                ),
                # Try adding new member (without giving role) -> this should use default role
                # Valid on try 1, invalid on try 2
                dict(
                    member=member_user4.pk,
                    clientId="member-user-4",
                ),
                dict(
                    id=membership_using_user_group.pk,
                    member=member_user7.pk,
                    clientId="member-user-2-with-user-group",
                    role=self.project_role_member.pk,
                    badges=[self.genum(ProjectMembership.BadgeType.QA)],
                ),
            ],
        )

        def _query_check(**kwargs):
            return self.query_check(
                query,
                mnested=["project"],
                variables={"id": project.id, **minput},
                **kwargs,
            )

        # ---------- Without login
        _query_check(assert_for_error=True)
        # ---------- With login (with non-member)
        self.force_login(non_member_user)
        _query_check(assert_for_error=True)
        # ---------- With login (with low-permission member)
        self.force_login(low_permission_user)
        _query_check(assert_for_error=True)
        # ---------- With login (with higher permission)
        self.force_login(user)
        # ----------------- Some Invalid input
        response = _query_check()["data"]["project"]["projectUserMembershipBulk"]
        self.assertMatchSnapshot(response, "try 1")
        # ----------------- Another try
        minput["projectMembership"].pop(1)
        minput["projectMembership"].extend(
            [
                # Invalid (changing member)
                dict(
                    member=member_user6.pk,
                    clientId="member-user-2",
                    role=self.project_role_owner.pk,
                    id=membership2.pk,
                ),
                dict(
                    member=member_user2.pk,
                    clientId="member-user-2",
                    role=self.project_role_admin.pk,
                    id=membership2.pk,
                ),
            ]
        )
        response = _query_check()["data"]["project"]["projectUserMembershipBulk"]
        self.assertMatchSnapshot(response, "try 2")
        # Check project change logs
        self.assertMatchSnapshot(
            list(ProjectChangeLog.objects.filter(project=project).order_by("id").values("action", "diff")),
            "project-change-log",
        )

    def test_user_membership_using_clairvoyan_one_bulk(self):
        self._user_membership_bulk(self.project_role_owner)

    def test_user_membership_admin_bulk(self):
        self._user_membership_bulk(self.project_role_admin)

    def _user_group_membership_bulk(self, user_role):
        query = """
          mutation MyMutation(
              $id: ID!,
              $projectMembership: [BulkProjectUserGroupMembershipInputType!],
              $projectMembershipDelete: [ID!]!
          ) {
          project(id: $id) {
            id
            title
            projectUserGroupMembershipBulk(items: $projectMembership, deleteIds: $projectMembershipDelete) {
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
                usergroup {
                  id
                  title
                }
                badges
              }
              deletedResult {
                id
                clientId
                joinedAt
                usergroup {
                  id
                  title
                }
                role {
                  id
                  title
                  level
                }
                addedBy {
                  id
                  displayName
                }
                badges
              }
            }
          }
        }
        """
        project = ProjectFactory.create()

        def _add_member(usergroup, role=None, badges=[]):
            return ProjectUserGroupMembership.objects.create(
                project=project,
                usergroup=usergroup,
                role_id=(role and role.id) or get_default_role_id(),
                badges=badges,
            )

        user = UserFactory.create()
        user_group = UserGroupFactory.create()
        user_group.members.add(user)

        (
            member_user_group0,
            member_user_group1,
            member_user_group2,
            member_user_group3,
            member_user_group4,
            member_user_group5,
            member_user_group6,
        ) = UserGroupFactory.create_batch(7)

        membership1 = _add_member(member_user_group1, badges=[ProjectMembership.BadgeType.QA])
        membership2 = _add_member(member_user_group2)
        _add_member(member_user_group5)
        another_clairvoyant_user_group = _add_member(member_user_group0, role=self.project_role_owner)
        user_group_membership = _add_member(user_group, role=user_role)

        minput = dict(
            projectMembershipDelete=[
                str(membership1.pk),  # This will be only on try 1
                # This shouldn't be on any response (requester + creater)
                str(user_group_membership.pk),
                str(another_clairvoyant_user_group.pk),
            ],
            projectMembership=[
                # Try updating membership (Valid on try 1, invalid on try 2)
                dict(
                    usergroup=member_user_group2.pk,
                    clientId="member-user-2",
                    role=self.project_role_owner.pk,
                    id=membership2.pk,
                    badges=[self.genum(ProjectMembership.BadgeType.QA)],
                ),
                # Try adding already existing member
                dict(
                    usergroup=member_user_group5.pk,
                    clientId="member-user-5",
                    role=self.project_role_member.pk,
                ),
                # Try adding new member (Valid on try 1, invalid on try 2)
                dict(
                    usergroup=member_user_group3.pk,
                    clientId="member-user-3",
                    role=self.project_role_member.pk,
                ),
                # Try adding new member (without giving role) -> this should use default role
                # Valid on try 1, invalid on try 2
                dict(
                    usergroup=member_user_group4.pk,
                    clientId="member-user-4",
                ),
            ],
        )

        def _query_check(**kwargs):
            return self.query_check(
                query,
                mnested=["project"],
                variables={"id": project.id, **minput},
                **kwargs,
            )

        # ---------- With login (with higher permission)
        self.force_login(user)
        # ----------------- Some Invalid input
        response = _query_check()["data"]["project"]["projectUserGroupMembershipBulk"]
        self.assertMatchSnapshot(response, "try 1")
        # ----------------- Another try
        minput["projectMembership"].pop(1)
        minput["projectMembership"].extend(
            [
                # Invalid (changing member)
                dict(
                    usergroup=member_user_group6.pk,
                    clientId="member-user-2",
                    role=self.project_role_owner.pk,
                    id=membership2.pk,
                ),
                dict(
                    usergroup=member_user_group2.pk,
                    clientId="member-user-2",
                    role=self.project_role_admin.pk,
                    id=membership2.pk,
                ),
            ]
        )
        response = _query_check()["data"]["project"]["projectUserGroupMembershipBulk"]
        self.assertMatchSnapshot(response, "try 2")
        # Check project change logs
        self.assertMatchSnapshot(
            list(ProjectChangeLog.objects.filter(project=project).order_by("id").values("action", "diff")),
            "project-change-log",
        )

    def test_user_group_membership_using_clairvoyan_one_bulk(self):
        self._user_group_membership_bulk(self.project_role_owner)

    def test_user_group_membership_admin_bulk(self):
        self._user_group_membership_bulk(self.project_role_admin)

    def test_project_deletion(self):
        query = """
            mutation MyMutation($projectId: ID!) {
              __typename
              project(id: $projectId) {
                  projectDelete {
                    ok
                    errors
                    result {
                      id
                      title
                    }
                  }
              }
            }
        """
        normal_user = UserFactory.create()
        admin_user = UserFactory.create()
        member_user = UserFactory.create()
        owner_user = UserFactory.create()
        reader_user = UserFactory.create()

        af = AnalysisFrameworkFactory.create()
        project = ProjectFactory.create(analysis_framework=af)

        project.add_member(admin_user, role=self.project_role_admin)
        project.add_member(member_user, role=self.project_role_member)
        project.add_member(owner_user, role=self.project_role_owner)
        project.add_member(reader_user, role=self.project_role_reader)

        def _assert_project_soft_delete_status(is_deleted):
            self.assertTrue(Project.objects.filter(pk=project.id).exists())
            project.refresh_from_db()
            if is_deleted:
                self.assertTrue(project.is_deleted)
                self.assertIsNotNone(project.deleted_at)
            else:
                self.assertFalse(project.is_deleted)
                self.assertIsNone(project.deleted_at)

        def _query_check(**kwargs):
            return self.query_check(
                query,
                mnested=["project"],
                variables={"projectId": project.id},
                **kwargs,
            )

        # without login
        _query_check(assert_for_error=True)
        _assert_project_soft_delete_status(False)

        # ------login and normal user
        self.force_login(normal_user)
        _query_check(assert_for_error=True)
        _assert_project_soft_delete_status(False)

        # ---------- With login and member_user in project
        self.force_login(member_user)
        _query_check(okay=False)
        _assert_project_soft_delete_status(False)

        # ---------- Login with reader user
        self.force_login(reader_user)
        _query_check(okay=False)
        _assert_project_soft_delete_status(False)

        # ------ Login with admin_user
        self.force_login(admin_user)
        _query_check(okay=False)
        _assert_project_soft_delete_status(False)

        # ------ Login with owner_user
        self.force_login(owner_user)
        _query_check(okay=True)
        _assert_project_soft_delete_status(True)
        # Check project change logs
        self.assertMatchSnapshot(
            list(ProjectChangeLog.objects.filter(project=project).order_by("id").values("action", "diff")),
            "project-change-log",
        )

    def test_project_deletion_celery_task(self):
        def _get_project_ids():
            return list(Project.objects.values_list("id", flat=True))

        # Check with single project
        project = ProjectFactory.create()
        # now delete the project
        project.soft_delete(deleted_at=self.now_datetime - timedelta(days=31))
        self.assertEqual(_get_project_ids(), [project.id])
        # call the deletion method
        permanently_delete_projects()
        self.assertEqual(_get_project_ids(), [])

        # Check with multiple projects
        project1 = ProjectFactory.create(
            title="Test Project 1", is_deleted=True, deleted_at=self.now_datetime - timedelta(days=32)
        )
        project2 = ProjectFactory.create(title="Test Project 2")
        project2_1 = ProjectFactory.create(
            title="Test Project 2 [Don't Delete']",
            deleted_at=self.now_datetime - timedelta(days=32),
        )
        project3 = ProjectFactory.create(
            title="Test Project 3",
            is_deleted=True,
            deleted_at=self.now_datetime - timedelta(days=42),
        )
        project4 = ProjectFactory.create(
            title="Test Project 4",
            is_deleted=True,
            deleted_at=self.now_datetime - timedelta(days=20),
        )
        project5 = ProjectFactory.create(
            title="Test Project 5",
            is_deleted=True,
            deleted_at=self.now_datetime - timedelta(days=30),
        )
        project6 = ProjectFactory.create(
            title="Test Project 6",
            is_deleted=True,
            deleted_at=self.now_datetime - timedelta(days=29),
        )

        permanently_delete_projects()

        # Check active projects ids
        project_ids = _get_project_ids()
        # Deleted projects.
        self.assertNotEqual(
            project_ids,
            [
                project1.id,
                project3.id,
            ],
        )
        self.assertEqual(
            project_ids,
            [
                project2.id,
                project2_1.id,
                project4.id,
                project5.id,
                project6.id,
            ],
        )

    def test_create_user_pinned_project(self):
        query = """
            mutation MyMutation($project: ID!) {
             createUserPinnedProject(data: {project: $project}) {
             ok
             errors
            result {
                clientId
                order
                user{
                    id
                }
                project{
                    id
                }
            }
         }
        }
        """
        project1 = ProjectFactory.create(
            title="Test Project 1",
        )
        project2 = ProjectFactory.create(
            title="Test Project 2",
        )
        member_user = UserFactory.create()
        owner_user = UserFactory.create()
        project1.add_member(member_user, role=self.project_role_member)
        project2.add_member(owner_user, role=self.project_role_owner)
        minput = dict(project=project1.id)

        def _query_check(**kwargs):
            return self.query_check(
                query,
                variables=minput,
                **kwargs,
            )

        self.force_login(member_user)
        response = _query_check()["data"]["createUserPinnedProject"]["result"]
        self.assertEqual(response["clientId"], str(project1.id))
        self.assertEqual(response["order"], 1)
        self.assertEqual(response["user"]["id"], str(member_user.id))
        self.assertEqual(response["project"]["id"], str(project1.id))
        # pin project which is already pinned by user
        response = _query_check(assert_for_error=True)["errors"]
        self.assertIn("Project already pinned!!", response[0]["message"])
        # pin another project
        minput["project"] = project2.id
        response = _query_check()["data"]["createUserPinnedProject"]["result"]
        self.assertEqual(response["clientId"], str(project2.id))
        self.assertEqual(response["order"], 2)
        self.assertEqual(response["project"]["id"], str(project2.id))

    def test_bulk_reorder_pinned_project(self):
        project1 = ProjectFactory.create(title="Test project 3")
        project2 = ProjectFactory.create(title="Test project 4")
        member_user = UserFactory.create()
        project1.add_member(member_user, role=self.project_role_member)
        project2.add_member(member_user, role=self.project_role_member)
        pinned_project1 = ProjectPinnedFactory.create(project=project1, user=member_user, order=10)
        # pinned_project2 = ProjectPinnedFactory.create(project=project2, user=member_user, order=12)
        minput = dict(order=14, id=pinned_project1.id)
        query = """
              mutation MyMutation($bulkReorder: UserPinnedProjectReOrderInputType!) {
              reorderPinnedProjects(items: $bulkReorder) {
                errors
                ok
                result {
                  clientId
                  order
                  project {
                    title
                    id
                  }
                  user {
                    id
                  }
                }
              }
            }
        """

        def _query_check(**kwargs):
            return self.query_check(query, variable=minput, **kwargs)

        self.force_login(member_user)
