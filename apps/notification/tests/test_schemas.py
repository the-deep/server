from utils.graphene.tests import GraphQLTestCase

from user.factories import UserFactory
from project.factories import ProjectFactory

from notification.models import Notification
from notification.factories import NotificationFactory


class TestNotificationQuerySchema(GraphQLTestCase):
    def test_notifications_query(self):
        """
        Test notification for users
        """
        query = '''
            query MyQuery {
              notifications {
                totalCount
                results {
                  id
                  status
                  project {
                    id
                    title
                  }
                  notificationType
                  timestamp
                  notificationTypeDisplay
                  statusDisplay
                  data
                }
              }
            }
        '''

        project = ProjectFactory.create()
        user = UserFactory.create()
        another_user = UserFactory.create()
        notification_meta = dict(
            notification_type=Notification.Type.PROJECT_JOIN_REQUEST,
            status=Notification.Status.UNSEEN,
        )
        NotificationFactory.create_batch(10, project=project, receiver=user, **notification_meta)
        NotificationFactory.create_batch(2, project=project, receiver=another_user, **notification_meta)

        def _query_check(**kwargs):
            return self.query_check(query, **kwargs)

        # -- Without login
        _query_check(assert_for_error=True)

        # --- With login
        self.force_login(user)
        content = _query_check()
        self.assertEqual(content['data']['notifications']['totalCount'], 10, content)
        self.assertEqual(len(content['data']['notifications']['results']), 10, content)

        self.force_login(another_user)
        content = _query_check()
        self.assertEqual(content['data']['notifications']['totalCount'], 2, content)
        self.assertEqual(len(content['data']['notifications']['results']), 2, content)

    def test_notification_query(self):
        query = '''
            query MyQuery ($id: ID!) {
              notification(id: $id) {
                  id
                  status
                  project {
                    id
                    title
                  }
                  notificationType
                  timestamp
                  notificationTypeDisplay
                  statusDisplay
                  data
              }
            }
        '''

        project = ProjectFactory.create()
        user = UserFactory.create()
        another_user = UserFactory.create()
        notification_meta = dict(
            notification_type=Notification.Type.PROJECT_JOIN_REQUEST,
            status=Notification.Status.UNSEEN,
        )
        our_notification = NotificationFactory.create(project=project, receiver=user, **notification_meta)
        other_notification = NotificationFactory.create(project=project, receiver=another_user, **notification_meta)

        def _query_check(notification, **kwargs):
            return self.query_check(query, variables={'id': notification.pk}, **kwargs)

        # -- Without login
        _query_check(our_notification, assert_for_error=True)

        # --- With login
        self.force_login(user)
        content = _query_check(our_notification)
        self.assertNotEqual(content['data']['notification'], None, content)

        content = _query_check(other_notification)
        self.assertEqual(content['data']['notification'], None, content)

    # TODO: Add test for filter
