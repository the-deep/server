from django.contrib.contenttypes.models import ContentType
from lead.factories import LeadFactory
from lead.models import Lead
from notification.factories import AssignmentFactory, NotificationFactory
from notification.models import Assignment, Notification
from project.factories import ProjectFactory
from user.factories import UserFactory

from utils.graphene.tests import GraphQLTestCase


class NotificationMutation(GraphQLTestCase):
    def test_notification_status_update(self):
        self.notification_query = """
            mutation Mutation($input: NotificationStatusInputType!) {
              notificationStatusUpdate(data: $input) {
                ok
                errors
                result {
                  id
                  status
                }
              }
            }
        """

        user = UserFactory.create()
        another_user = UserFactory.create()
        notification = NotificationFactory.create(status=Notification.Status.UNSEEN, receiver=user)

        def _query_check(minput, **kwargs):
            return self.query_check(self.notification_query, minput=minput, **kwargs)

        minput = dict(id=notification.id, status=self.genum(Notification.Status.SEEN))
        # -- Without login
        _query_check(minput, assert_for_error=True)

        # -- With login
        self.force_login(user)
        content = _query_check(minput)
        self.assertEqual(content["data"]["notificationStatusUpdate"]["errors"], None, content)

        # check for the notification status update(db-level)
        notification = Notification.objects.get(id=notification.id)
        assert notification.status == Notification.Status.SEEN

        # -- with different user
        self.force_login(another_user)
        content = _query_check(minput, okay=False)["data"]["notificationStatusUpdate"]["result"]
        self.assertEqual(content, None, content)


class TestAssignmentMutation(GraphQLTestCase):
    def test_assginment_bulk_status_mark_as_done(self):
        self.assignment_query = """
            mutation MyMutation {
                assignmentBulkStatusMarkAsDone {
                    errors
                    ok
                }
            }
        """
        project = ProjectFactory.create()
        user = UserFactory.create()
        lead = LeadFactory.create()
        AssignmentFactory.create_batch(
            3,
            project=project,
            object_id=lead.id,
            content_type=ContentType.objects.get_for_model(Lead),
            created_for=user,
            is_done=False,
        )

        def _query_check(**kwargs):
            return self.query_check(self.assignment_query, **kwargs)

        self.force_login(user)
        content = _query_check()
        assignments_qs = Assignment.get_for(user).filter(is_done=False)
        self.assertEqual(content["data"]["assignmentBulkStatusMarkAsDone"]["errors"], None)
        self.assertEqual(len(assignments_qs), 0)

    def test_individual_assignment_update_status(self):
        self.indivdual_assignment_query = """
            mutation Mutation($isDone: Boolean, $id: ID! ){
                assignmentUpdate(id: $id, data: {isDone: $isDone}){
                    ok
                    errors
                    result{
                        id
                        isDone
                    }
                }
            }
        """

        user = UserFactory.create()
        project = ProjectFactory.create()
        lead = LeadFactory.create()
        assignment = AssignmentFactory.create(
            project=project,
            object_id=lead.id,
            content_type=ContentType.objects.get_for_model(Lead),
            created_for=user,
            is_done=False,
        )

        def _query_check(**kwargs):
            return self.query_check(self.indivdual_assignment_query, variables={"isDone": True, "id": assignment.id}, **kwargs)

        # without login

        _query_check(assert_for_error=True)

        # with normal login

        self.force_login(user)
        content = _query_check()
        assignment_qs = Assignment.get_for(user).filter(id=assignment.id, is_done=False)
        self.assertEqual(content["data"]["assignmentUpdate"]["errors"], None)
        self.assertEqual(len(assignment_qs), 0)
