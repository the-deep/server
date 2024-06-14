from unittest import mock

from gallery.factories import FileFactory
from lead.factories import (
    EmmEntityFactory,
    LeadEMMTriggerFactory,
    LeadFactory,
    LeadGroupFactory,
    LeadPreviewFactory,
    LeadPreviewImageFactory,
)
from lead.models import Lead
from organization.factories import OrganizationFactory
from project.factories import ProjectFactory
from user.factories import UserFactory

from utils.graphene.tests import GraphQLSnapShotTestCase, GraphQLTestCase


class TestLeadMutationSchema(GraphQLTestCase):
    CREATE_LEAD_QUERY = """
        mutation MyMutation ($projectId: ID!, $input: LeadInputType!) {
          project(id: $projectId) {
            leadCreate1: leadCreate(data: $input) {
              ok
              errors
              result {
                id
                title
                confidentiality
                priority
                publishedOn
                sourceType
                status
                text
                url
                source {
                    id
                }
                authors {
                    id
                }
                assignee {
                    id
                }
                emmEntities {
                    name
                }
                emmTriggers {
                    emmKeyword
                    emmRiskFactor
                    count
                }
              }
            }
          }
        }
    """

    def setUp(self):
        super().setUp()
        self.project = ProjectFactory.create()
        # User with role
        self.non_member_user = UserFactory.create()
        self.readonly_member_user = UserFactory.create()
        self.member_user = UserFactory.create()
        self.project.add_member(self.readonly_member_user, role=self.project_role_reader_non_confidential)
        self.project.add_member(self.member_user, role=self.project_role_member)

    @mock.patch("lead.serializers.index_lead_and_calculate_duplicates.delay")
    def test_lead_create(self, index_and_calculate_dups_func):
        """
        This test makes sure only valid users can create lead
        """

        def _query_check(minput, **kwargs):
            with self.captureOnCommitCallbacks(execute=True):
                return self.query_check(self.CREATE_LEAD_QUERY, minput=minput, variables={"projectId": self.project.id}, **kwargs)

        minput = dict(
            title="Lead Title 101",
        )
        # -- Without login
        _query_check(minput, assert_for_error=True)

        # -- With login (non-member)
        self.force_login(self.non_member_user)
        _query_check(minput, assert_for_error=True)

        # --- member user (read-only)
        self.force_login(self.readonly_member_user)
        _query_check(minput, assert_for_error=True)

        # --- member user
        self.force_login(self.member_user)
        content = _query_check(minput)["data"]["project"]["leadCreate1"]["result"]
        self.assertEqual(content["title"], minput["title"], content)

        index_and_calculate_dups_func.assert_called()

    def test_lead_create_validation(self):
        """
        This test checks create lead validations
        """
        other_file = FileFactory.create()
        our_file = FileFactory.create(created_by=self.member_user)
        org1 = OrganizationFactory.create()
        org2 = OrganizationFactory.create()

        emm_entity_1 = EmmEntityFactory.create()
        emm_entity_2 = EmmEntityFactory.create()

        minput = dict(
            title="Lead Title 101",
            confidentiality=self.genum(Lead.Confidentiality.UNPROTECTED),
            priority=self.genum(Lead.Priority.MEDIUM),
            status=self.genum(Lead.Status.NOT_TAGGED),
            publishedOn="2020-09-25",
            source=org2.pk,
            authors=[org1.pk, org2.pk],
            text="Random Text",
            url="",
            emmEntities=[
                dict(name=emm_entity_1.name),
                dict(name=emm_entity_2.name),
            ],
            emmTriggers=[
                # Return order is by count so let's keep higher count first
                dict(emmKeyword="emm-keyword-1", emmRiskFactor="emm-risk-factor-1", count=20),
                dict(emmKeyword="emm-keyword-2", emmRiskFactor="emm-risk-factor-2", count=10),
            ],
        )

        def _query_check(**kwargs):
            return self.query_check(
                self.CREATE_LEAD_QUERY,
                minput=minput,
                mnested=["project"],
                variables={"projectId": self.project.id},
                **kwargs,
            )

        # --- login
        self.force_login(self.member_user)

        # ------ Non member assignee
        minput["sourceType"] = self.genum(Lead.SourceType.TEXT)
        minput["text"] = "Text 123"
        minput["assignee"] = self.non_member_user.pk
        result = _query_check(okay=False)["data"]["project"]["leadCreate1"]["result"]
        self.assertEqual(result, None, result)
        # ------ Member assignee (TODO: Test partial update as well) + Text Test
        minput["assignee"] = self.member_user.pk
        minput["text"] = "Text 123123"  # Need to provide different text
        result = _query_check(okay=True)["data"]["project"]["leadCreate1"]["result"]
        self.assertIdEqual(result["assignee"]["id"], minput["assignee"], result)
        self.assertCustomDictEqual(result, minput, result, ignore_keys=["id", "source", "authors", "assignee"])
        self.assertIdEqual(result["source"]["id"], minput["source"], result)
        self.assertListIds(result["authors"], minput["authors"], result, get_excepted_list_id=lambda x: str(x))
        # ------ Disk
        # File not-owned
        minput["sourceType"] = self.genum(Lead.SourceType.DISK)
        minput["attachment"] = other_file.pk
        result = _query_check(okay=False)["data"]["project"]["leadCreate1"]["result"]
        self.assertEqual(result, None, result)
        # File owned
        minput["sourceType"] = self.genum(Lead.SourceType.DISK)
        minput["attachment"] = our_file.pk
        result = _query_check(okay=True)["data"]["project"]["leadCreate1"]["result"]
        self.assertEqual(result["title"], minput["title"], result)

        # -------- Duplicate leads validations
        # ------------- Text (Using duplicate text)
        minput["sourceType"] = self.genum(Lead.SourceType.TEXT)
        result = _query_check(okay=False)["data"]["project"]["leadCreate1"]["result"]
        self.assertEqual(result, None, result)
        # ------------- Website
        minput["sourceType"] = self.genum(Lead.SourceType.WEBSITE)
        minput["url"] = "http://www.example.com/random-path"
        result = _query_check(okay=True)["data"]["project"]["leadCreate1"]["result"]
        self.assertCustomDictEqual(result, minput, result, only_keys=["url"])
        # Try again will end in error
        result = _query_check(okay=False)["data"]["project"]["leadCreate1"]["result"]
        self.assertEqual(result, None, result)
        # ------------- Attachment
        minput["sourceType"] = self.genum(Lead.SourceType.DISK)
        minput["attachment"] = our_file.pk  # Already created this above resulting in error
        result = _query_check(okay=False)["data"]["project"]["leadCreate1"]["result"]
        self.assertEqual(result, None, result)

    @mock.patch("lead.receivers.update_index_and_duplicates")
    def test_lead_delete_validation(self, update_indices_func):
        """
        This test checks create lead validations
        """
        query = """
            mutation MyMutation ($projectId: ID! $leadId: ID!) {
              project(id: $projectId) {
                leadDelete(id: $leadId) {
                  ok
                  errors
                  result {
                    id
                    title
                    url
                  }
                }
              }
            }
        """

        non_access_lead = LeadFactory.create()
        lead = LeadFactory.create(project=self.project)

        def _query_check(lead, will_delete=False, **kwargs):
            with self.captureOnCommitCallbacks(execute=True):
                result = self.query_check(
                    query,
                    mnested=["project"],
                    variables={"projectId": self.project.id, "leadId": lead.id},
                    **kwargs,
                )
            if will_delete:
                with self.assertRaises(Lead.DoesNotExist):
                    lead.refresh_from_db()
            else:
                lead.refresh_from_db()
            return result

        # Error without login
        _query_check(non_access_lead, assert_for_error=True)

        # --- login
        self.force_login(self.member_user)
        # Error with login (if non-member project)
        _query_check(non_access_lead, okay=False)
        # ------- login as readonly_member
        self.force_login(self.readonly_member_user)
        # No Success with normal lead (with project membership)
        _query_check(lead, assert_for_error=True)
        # ------- login as normal member
        self.force_login(self.member_user)
        # Success with normal lead (with project membership)
        result = _query_check(lead, will_delete=True, okay=True)["data"]["project"]["leadDelete"]["result"]
        self.assertEqual(result["title"], lead.title, result)
        update_indices_func.assert_called_once()

    def test_lead_update_validation(self):
        query = """
            mutation MyMutation ($projectId: ID! $leadId: ID! $input: LeadInputType!) {
              project(id: $projectId) {
                leadUpdate(id: $leadId data: $input) {
                  ok
                  errors
                  result {
                    id
                    title
                    sourceType
                    text
                    url
                    attachment {
                        id
                    }
                    assignee {
                        id
                    }
                    emmEntities {
                        name
                    }
                    emmTriggers {
                        emmKeyword
                        emmRiskFactor
                        count
                    }
                  }
                }
              }
            }
        """

        lead = LeadFactory.create(project=self.project)
        non_access_lead = LeadFactory.create()
        user_file = FileFactory.create(created_by=self.member_user)

        minput = dict(title="New Lead")

        def _query_check(_lead, **kwargs):
            return self.query_check(
                query,
                minput=minput,
                mnested=["project"],
                variables={"projectId": self.project.id, "leadId": _lead.id},
                **kwargs,
            )

        # --- without login
        _query_check(lead, assert_for_error=True)

        # --- login
        self.force_login(self.member_user)
        # ------- Non access lead
        _query_check(non_access_lead, okay=False)
        # ------- Access lead
        result = _query_check(lead, okay=True)["data"]["project"]["leadUpdate"]["result"]
        self.assertEqual(result["title"], minput["title"], result)
        # -------- Duplicate leads validations
        # ------------ Text (Using duplicate text)
        new_lead = LeadFactory.create(project=self.project)
        minput["sourceType"] = self.genum(Lead.SourceType.TEXT)
        minput["text"] = new_lead.text
        result = _query_check(lead, okay=False)["data"]["project"]["leadUpdate"]["result"]
        self.assertEqual(result, None, result)
        new_lead.delete()  # Can save after deleting the conflicting lead.
        result = _query_check(lead, okay=True)["data"]["project"]["leadUpdate"]["result"]
        self.assertEqual(result["title"], minput["title"], result)
        # ------------ Website (Using duplicate website)
        new_lead = LeadFactory.create(
            project=self.project, source_type=Lead.SourceType.WEBSITE, url="https://example.com/random-path"
        )
        minput["sourceType"] = self.genum(Lead.SourceType.WEBSITE)
        minput["url"] = new_lead.url
        result = _query_check(lead, okay=False)["data"]["project"]["leadUpdate"]["result"]
        self.assertEqual(result, None, result)
        new_lead.delete()  # Can save after deleting the conflicting lead.
        result = _query_check(lead, okay=True)["data"]["project"]["leadUpdate"]["result"]
        self.assertEqual(result["url"], minput["url"], result)
        # ------------ Attachment (Using duplicate file)
        new_lead = LeadFactory.create(project=self.project, source_type=Lead.SourceType.DISK, attachment=user_file)
        minput["sourceType"] = self.genum(Lead.SourceType.DISK)
        minput["attachment"] = new_lead.attachment.pk
        result = _query_check(lead, okay=False)["data"]["project"]["leadUpdate"]["result"]
        self.assertEqual(result, None, result)
        new_lead.delete()  # Can save after deleting the conflicting lead.
        result = _query_check(lead, okay=True)["data"]["project"]["leadUpdate"]["result"]
        self.assertIdEqual(result["attachment"]["id"], minput["attachment"], result)


class TestLeadBulkMutationSchema(GraphQLSnapShotTestCase):
    factories_used = [UserFactory, ProjectFactory, LeadFactory]

    def test_lead_bulk(self):
        query = """
        mutation MyMutation ($projectId: ID! $input: [BulkLeadInputType!]) {
          project(id: $projectId) {
            leadBulk(items: $input) {
              errors
              result {
                id
                title
                clientId
              }
            }
          }
        }
        """
        project = ProjectFactory.create()
        # User with role
        user = UserFactory.create()
        project.add_member(user, role=self.project_role_member)
        lead1 = LeadFactory.create(project=project)
        lead2 = LeadFactory.create(project=project, source_type=Lead.SourceType.WEBSITE, url="https://example.com/path")

        lead_count = Lead.objects.count()
        minput = [
            dict(title="Lead title 1", clientId="new-lead-1"),
            dict(title="Lead title 2", clientId="new-lead-2"),
            dict(
                title="Lead title 4",
                sourceType=self.genum(Lead.SourceType.WEBSITE),
                url="https://example.com/path",
                clientId="new-lead-3",
            ),
            dict(id=str(lead1.pk), title="Lead title 3"),
            dict(id=str(lead2.pk), title="Lead title 4"),
        ]

        def _query_check(**kwargs):
            return self.query_check(query, minput=minput, variables={"projectId": project.pk}, **kwargs)

        # --- without login
        _query_check(assert_for_error=True)

        # --- with login
        self.force_login(user)
        response = _query_check()["data"]["project"]["leadBulk"]
        self.assertMatchSnapshot(response, "success")
        self.assertEqual(lead_count + 2, Lead.objects.count())


class TestLeadGroupMutation(GraphQLTestCase):
    def test_lead_group_delete(self):
        query = """
            mutation MyMutation ($projectId: ID! $leadGroupId: ID!) {
              project(id: $projectId) {
                leadGroupDelete(id: $leadGroupId) {
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
        project = ProjectFactory.create()
        member_user = UserFactory.create()
        non_member_user = UserFactory.create()
        project.add_member(member_user)
        lead_group = LeadGroupFactory.create(project=project)

        def _query_check(**kwargs):
            return self.query_check(query, variables={"projectId": project.id, "leadGroupId": lead_group.id}, **kwargs)

        # -- Without login
        _query_check(assert_for_error=True)

        # --- member user
        self.force_login(member_user)
        content = _query_check()
        self.assertEqual(content["data"]["project"]["leadGroupDelete"]["ok"], True)
        self.assertIdEqual(content["data"]["project"]["leadGroupDelete"]["result"]["id"], lead_group.id)

        # -- non-member user
        self.force_login(non_member_user)
        _query_check(assert_for_error=True)


class TestLeadCopyMutation(GraphQLTestCase):
    def test_lead_copy_mutation(self):
        query = """
            mutation MyMutation ($projectId: ID! $input: LeadCopyInputType!) {
              project(id: $projectId) {
                leadCopy(data: $input) {
                  ok
                  errors
                  result {
                    id
                    title
                    project
                    status
                    createdAt
                    createdBy {
                        id
                    }
                    modifiedBy {
                        id
                    }
                  }
                }
              }
            }
        """
        member_user = UserFactory.create()
        member_user_only_protected = UserFactory.create()
        non_member_user = UserFactory.create()
        created_by_user = UserFactory.create()

        # Source Projects
        wa_source_project = ProjectFactory.create(title="With access Source Project")  # With access
        woa_source_project = ProjectFactory.create(title="Without access Source Project")  # Without access
        # Destination Projects
        wa_destination_project = ProjectFactory.create(title="With access Destination Project")  # With access
        woa_destination_project = ProjectFactory.create(title="Without access Destination Project")  # Without access
        # Assign access
        wa_source_project.add_member(member_user)
        wa_source_project.add_member(member_user_only_protected, role=self.project_role_reader_non_confidential)
        wa_destination_project.add_member(member_user)
        wa_destination_project.add_member(member_user_only_protected)
        woa_source_project.add_member(member_user, role=self.project_base_access)  # With no lead read access
        woa_source_project.add_member(member_user_only_protected, role=self.project_base_access)  # With no lead read access

        # Lead1 Info (Will be used later for testing)
        author1 = OrganizationFactory.create(title="author1")
        author2 = OrganizationFactory.create(title="author2")
        emm_entity = EmmEntityFactory.create(name="emm_entity_11")

        # Generate some leads in source projects.
        wa_lead_confidential = LeadFactory.create(
            title="Confidential Lead (with-access)",
            project=wa_source_project,
            source_type=Lead.SourceType.WEBSITE,
            url="http://confidential-lead.example.com",
            confidentiality=Lead.Confidentiality.CONFIDENTIAL,
        )
        wa_lead1 = LeadFactory.create(
            title="Lead 1 (with-access)",
            project=wa_source_project,
            source_type=Lead.SourceType.WEBSITE,
            url="http://example.com",
            created_by=created_by_user,
            status=Lead.Status.TAGGED,
        )
        wa_lead2 = LeadFactory.create(
            title="Lead 2 (with-access)",
            project=wa_source_project,
            source_type=Lead.SourceType.WEBSITE,
            url="http://another.example.com",
        )
        woa_lead3 = LeadFactory.create(
            title="Lead 3 (without-access)",
            project=woa_source_project,
            source_type=Lead.SourceType.WEBSITE,
            url="http://another-2.example.com",
        )
        # Assign authors
        wa_lead1.authors.set([author1, author2])
        wa_lead2.authors.set([author1])
        woa_lead3.authors.set([author2])

        # Generating Foreign elements for wa_lead1
        wa_lead1_preview = LeadPreviewFactory.create(lead=wa_lead1, text_extract="This is a random text extarct")
        wa_lead1_image_preview = LeadPreviewImageFactory.create(lead=wa_lead1, file="test-file-123")
        LeadEMMTriggerFactory.create(
            lead=wa_lead1,
            emm_keyword="emm1",
            emm_risk_factor="risk1",
            count=22,
        )
        wa_lead1.emm_entities.set([emm_entity])

        # Generate some leads in destinations projects as well.
        LeadFactory.create(
            project=wa_destination_project,
            title=wa_lead2.title,
            source_type=wa_lead2.source_type,
            url=wa_lead2.url,
        )

        # test for single lead copy
        minput = {
            "projects": [
                wa_destination_project.id,  # Lead will be added here
                woa_destination_project.id,  # No Lead are added here
            ],
            "leads": [wa_lead_confidential.id, wa_lead1.id, wa_lead2.id, woa_lead3.id],
        }

        def _query_check(source_project, **kwargs):
            return self.query_check(query, minput=minput, variables={"projectId": source_project.pk}, **kwargs)

        # without login
        _query_check(wa_source_project, assert_for_error=True)

        # with non_member user[destination_project]
        self.force_login(non_member_user)
        _query_check(wa_source_project, assert_for_error=True)

        # with member user (With non-confidential access)
        self.force_login(member_user_only_protected)

        woa_current_leads_count = woa_destination_project.lead_set.count()
        woa_current_leads_count = woa_destination_project.lead_set.count()
        # Call endpoint using no lead read access (no changes here)
        _query_check(woa_source_project, okay=False)
        woa_new_leads_count = woa_destination_project.lead_set.count()
        self.assertEqual(woa_current_leads_count, woa_new_leads_count)
        self.assertEqual(woa_current_leads_count, woa_new_leads_count)

        wa_current_leads_count = wa_destination_project.lead_set.count()
        woa_current_leads_count = woa_destination_project.lead_set.count()
        # Call endpoint
        new_leads = _query_check(wa_source_project)["data"]["project"]["leadCopy"]["result"]
        # lets make sure lead is copied to the destination project
        wa_new_count = wa_destination_project.lead_set.count()
        woa_new_leads_count = woa_destination_project.lead_set.count()
        # Only 1 since there is already another lead for wa_lead2 in wa_destination_project
        # confidential can't be copied for member_user_only_protected user.
        self.assertEqual(len(new_leads), 1, new_leads)
        self.assertEqual(wa_new_count, wa_current_leads_count + 1)
        self.assertEqual(woa_current_leads_count, woa_new_leads_count)

        wa_current_leads_count = wa_destination_project.lead_set.count()
        woa_current_leads_count = woa_destination_project.lead_set.count()
        # Call endpoint (again)
        _query_check(wa_source_project)
        wa_new_count = wa_destination_project.lead_set.count()
        woa_new_leads_count = woa_destination_project.lead_set.count()
        # No changes now since leads are already copied
        self.assertEqual(wa_new_count, wa_current_leads_count)
        self.assertEqual(woa_current_leads_count, woa_new_leads_count)

        self.force_login(member_user)  # With confidential access
        wa_current_leads_count = wa_destination_project.lead_set.count()
        woa_current_leads_count = woa_destination_project.lead_set.count()
        # Call endpoint
        _query_check(wa_source_project)
        # lets make sure lead is copied to the destination project
        wa_new_count = wa_destination_project.lead_set.count()
        woa_new_leads_count = woa_destination_project.lead_set.count()
        self.assertEqual(wa_new_count, wa_current_leads_count + 1)  # 1 new confidential lead
        self.assertEqual(woa_current_leads_count, woa_new_leads_count)

        # Now check if copied leads are done correctly
        # make sure same lead is created for destination project
        copied_lead1 = wa_destination_project.lead_set.get(title=wa_lead1.title)
        self.assertEqual(copied_lead1.source_type, wa_lead1.source_type)
        self.assertEqual(copied_lead1.url, wa_lead1.url)
        self.assertEqual(copied_lead1.confidentiality, wa_lead1.confidentiality)
        # lets check for the foreign key field copy
        self.assertEqual(copied_lead1.leadpreview.text_extract, wa_lead1_preview.text_extract)
        self.assertEqual(list(copied_lead1.images.values_list("file", flat=True)), [wa_lead1_image_preview.file.name])
        self.assertEqual(
            list(copied_lead1.emm_triggers.values("emm_keyword", "emm_risk_factor", "count")),
            list(wa_lead1.emm_triggers.values("emm_keyword", "emm_risk_factor", "count")),
        )
        self.assertEqual(
            list(copied_lead1.emm_entities.all()),
            [emm_entity],
        )
        # lets check for the updated fields after copy
        self.assertEqual(copied_lead1.created_by.id, member_user_only_protected.id)
        self.assertEqual(copied_lead1.modified_by.id, member_user_only_protected.id)
        self.assertEqual(copied_lead1.status, Lead.Status.NOT_TAGGED)
