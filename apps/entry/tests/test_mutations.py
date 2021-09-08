from django.utils import timezone

from utils.graphene.tests import GraphQLSnapShotTestCase

from entry.models import Entry

from user.factories import UserFactory
from entry.factories import EntryFactory, EntryAttriuteFactory
from project.factories import ProjectFactory
from lead.factories import LeadFactory
from analysis_framework.factories import AnalysisFrameworkFactory, WidgetFactory
from gallery.factories import FileFactory


class TestEntryMutation(GraphQLSnapShotTestCase):
    """
    TODO:
    - Make sure only 1 attribute is allowed for one widget
    """
    factories_used = [FileFactory]

    CREATE_ENTRY_QUERY = '''
        mutation MyMutation ($projectId: ID!, $input: EntryInputType!) {
          project(id: $projectId) {
            entryCreate(data: $input) {
              errors
              ok
              result {
                id
                clientId
                droppedExcerpt
                entryType
                excerpt
                highlightHidden
                image {
                  id
                  title
                }
                informationDate
                order
                attributes {
                  id
                  widget
                  widgetType
                  data
                  clientId
                }
              }
            }
          }
        }
    '''

    UPDATE_ENTRY_QUERY = '''
        mutation MyMutation ($projectId: ID!, $entryId: ID!, $input: EntryInputType!) {
          project(id: $projectId) {
            entryUpdate(id: $entryId data: $input) {
              errors
              ok
              result {
                id
                clientId
                droppedExcerpt
                entryType
                excerpt
                highlightHidden
                image {
                  id
                  title
                }
                informationDate
                order
                attributes {
                  id
                  widget
                  widgetType
                  data
                  clientId
                }
              }
            }
          }
        }
    '''

    DELETE_ENTRY_QUERY = '''
        mutation MyMutation ($projectId: ID!, $entryId: ID!) {
          project(id: $projectId) {
            entryDelete(id: $entryId) {
              errors
              ok
              result {
                id
                clientId
                droppedExcerpt
                entryType
                excerpt
                highlightHidden
                image {
                  id
                  title
                }
                informationDate
                order
                attributes {
                  id
                  widget
                  widgetType
                  data
                  clientId
                }
              }
            }
          }
        }
    '''

    BULK_ENTRY_QUERY = '''
        mutation MyMutation ($projectId: ID!, $deleteIds: [ID!], $items: [BulkEntryInputType!]) {
          project(id: $projectId) {
            entryBulk(deleteIds: $deleteIds items: $items) {
              errors
              deletedResult {
                id
                clientId
                droppedExcerpt
                entryType
                excerpt
                highlightHidden
                image {
                  id
                  title
                }
                informationDate
                order
                attributes {
                  id
                  widget
                  widgetType
                  data
                  clientId
                }
              }
              result {
                id
                clientId
                droppedExcerpt
                entryType
                excerpt
                highlightHidden
                image {
                  id
                  title
                }
                informationDate
                order
                attributes {
                  id
                  widget
                  widgetType
                  data
                  clientId
                }
              }
            }
          }
        }
    '''

    def setUp(self):
        super().setUp()
        self.af = AnalysisFrameworkFactory.create()
        self.project = ProjectFactory.create(analysis_framework=self.af)
        # User with role
        self.non_member_user = UserFactory.create()
        self.readonly_member_user = UserFactory.create()
        self.member_user = UserFactory.create()
        self.project.add_member(self.readonly_member_user, role=self.project_role_viewer_non_confidential)
        self.project.add_member(self.member_user, role=self.project_role_analyst)
        self.lead = LeadFactory.create(project=self.project)
        self.widget1 = WidgetFactory.create(analysis_framework=self.af)
        self.widget2 = WidgetFactory.create(analysis_framework=self.af)
        self.widget3 = WidgetFactory.create(analysis_framework=self.af)
        # Files
        self.other_file = FileFactory.create()
        self.our_file = FileFactory.create(created_by=self.member_user)
        self.dummy_data = dict({})

    def test_entry_create(self):
        """
        This test makes sure only valid users can create entry
        """
        minput = dict(
            attributes=[
                dict(widget=self.widget1.pk, data=self.dummy_data, clientId='client-id-attribute-1'),
                dict(widget=self.widget2.pk, data=self.dummy_data, clientId='client-id-attribute-2'),
                dict(widget=self.widget3.pk, data=self.dummy_data, clientId='client-id-attribute-3'),
            ],
            order=1,
            lead=self.lead.pk,
            informationDate=self.get_date_str(timezone.now()),
            image=self.other_file.pk,
            # leadImage='',
            highlightHidden=False,
            excerpt='This is a text',
            entryType=self.genum(Entry.TagType.EXCERPT),
            droppedExcerpt='This is a dropped text',
            clientId='entry-101',
        )

        def _query_check(**kwargs):
            return self.query_check(
                self.CREATE_ENTRY_QUERY,
                minput=minput,
                variables={'projectId': self.project.id},
                **kwargs
            )

        # -- Without login
        _query_check(assert_for_error=True)

        # -- With login (non-member)
        self.force_login(self.non_member_user)
        _query_check(assert_for_error=True)

        # --- member user (read-only)
        self.force_login(self.readonly_member_user)
        _query_check(assert_for_error=True)

        # --- member user
        # Invalid input
        self.force_login(self.member_user)
        response = _query_check(okay=False)
        self.assertMatchSnapshot(response, 'error')

        # Valid input
        minput['image'] = self.our_file.pk
        response = _query_check()
        self.assertMatchSnapshot(response, 'success')

    def test_entry_update(self):
        """
        This test makes sure only valid users can update entry
        """
        entry = EntryFactory.create(project=self.project, lead=self.lead, analysis_framework=self.project.analysis_framework)

        minput = dict(
            attributes=[
                dict(widget=self.widget1.pk, data=self.dummy_data, clientId='client-id-attribute-1'),
                dict(widget=self.widget2.pk, data=self.dummy_data, clientId='client-id-attribute-2'),
                dict(widget=self.widget1.pk, data=self.dummy_data, clientId='client-id-attribute-3'),
            ],
            order=1,
            lead=self.lead.pk,
            informationDate=self.get_date_str(timezone.now()),
            image=self.other_file.pk,
            # leadImage='',
            highlightHidden=False,
            excerpt='This is a text',
            entryType=self.genum(Entry.TagType.EXCERPT),
            droppedExcerpt='This is a dropped text',
            clientId='entry-101',
        )

        def _query_check(**kwargs):
            return self.query_check(
                self.UPDATE_ENTRY_QUERY,
                minput=minput,
                variables={'projectId': self.project.id, 'entryId': entry.id},
                **kwargs
            )

        # -- Without login
        _query_check(assert_for_error=True)

        # -- With login (non-member)
        self.force_login(self.non_member_user)
        _query_check(assert_for_error=True)

        # --- member user (read-only)
        self.force_login(self.readonly_member_user)
        _query_check(assert_for_error=True)

        # --- member user
        # Invalid input
        self.force_login(self.member_user)
        response = _query_check(okay=False)
        self.assertMatchSnapshot(response, 'error')

        # Valid input
        minput['image'] = self.our_file.pk
        response = _query_check()
        self.assertMatchSnapshot(response, 'success')

    def test_entry_delete(self):
        """
        This test makes sure only valid users can update entry
        """
        entry = EntryFactory.create(project=self.project, lead=self.lead, analysis_framework=self.project.analysis_framework)

        def _query_check(**kwargs):
            return self.query_check(
                self.DELETE_ENTRY_QUERY,
                variables={'projectId': self.project.id, 'entryId': entry.id},
                **kwargs
            )

        # -- Without login
        _query_check(assert_for_error=True)

        # -- With login (non-member)
        self.force_login(self.non_member_user)
        _query_check(assert_for_error=True)

        # --- member user (read-only)
        self.force_login(self.readonly_member_user)
        _query_check(assert_for_error=True)

        # --- member user
        # Invalid input
        self.force_login(self.member_user)
        content = _query_check(okay=False)['data']['project']['entryDelete']['result']
        self.assertIdEqual(content['id'], entry.id)

    def test_entry_bulk(self):
        """
        This test makes sure only valid users can bulk create/update/delete entry
        """
        entry1, entry2 = EntryFactory.create_batch(
            2,
            project=self.project, lead=self.lead, analysis_framework=self.project.analysis_framework
        )
        entry2_att1 = EntryAttriuteFactory.create(entry=entry2, widget=self.widget1, data=self.dummy_data)

        minput = dict(
            deleteIds=[entry1.pk],
            items=[
                dict(
                    id=entry2.pk,
                    attributes=[
                        dict(widget=self.widget1.pk, data=self.dummy_data, clientId='client-id-old-new-attribute-1'),
                        dict(
                            id=entry2_att1.pk,
                            widget=self.widget1.pk, data=self.dummy_data, clientId='client-id-old-attribute-1'
                        ),
                    ],
                    order=1,
                    lead=self.lead.pk,
                    informationDate=self.get_date_str(timezone.now()),
                    image=self.other_file.pk,
                    # leadImage='',
                    highlightHidden=False,
                    excerpt='This is a text (UPDATED)',
                    entryType=self.genum(Entry.TagType.EXCERPT),
                    droppedExcerpt='This is a dropped text (UPDATED)',
                    clientId='entry-old-101 (UPDATED)',
                ),
                dict(
                    attributes=[
                        dict(widget=self.widget1.pk, data=self.dummy_data, clientId='client-id-new-attribute-1'),
                    ],
                    order=1,
                    lead=self.lead.pk,
                    informationDate=self.get_date_str(timezone.now()),
                    image=self.other_file.pk,
                    # leadImage='',
                    highlightHidden=False,
                    excerpt='This is a text (NEW)',
                    entryType=self.genum(Entry.TagType.EXCERPT),
                    droppedExcerpt='This is a dropped text (NEW)',
                    clientId='entry-new-102',
                )
            ],
        )

        def _query_check(**kwargs):
            return self.query_check(
                self.BULK_ENTRY_QUERY,
                variables={'projectId': self.project.id, **minput},
                **kwargs
            )

        print(entry1, entry2)
        # -- Without login
        _query_check(assert_for_error=True)

        # -- With login (non-member)
        self.force_login(self.non_member_user)
        _query_check(assert_for_error=True)

        # --- member user (read-only)
        self.force_login(self.readonly_member_user)
        _query_check(assert_for_error=True)

        # --- member user
        self.force_login(self.member_user)
        # Invalid input
        response = _query_check(okay=False)
        self.assertMatchSnapshot(response, 'error')

        # Valid input
        minput['items'][0]['image'] = self.our_file.pk
        minput['items'][1]['image'] = self.our_file.pk
        response = _query_check()
        self.assertMatchSnapshot(response, 'success')

    # TODO: Add test for other entry attributes id as well
