import datetime
import pytz

from utils.graphene.tests import GraphQLTestCase
from user.factories import UserFactory
from project.factories import ProjectFactory

from notification.models import Notification
from notification.factories import AssignmentFactory, NotificationFactory
from lead.factories import LeadFactory


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

    def test_notifications_with_filter_query(self):
        query = '''
            query MyQuery (
                $timestamp: DateTime,
                $timestampLte: DateTime,
                $timestampGte: DateTime,
                $status: NotificationStatusEnum,
                $notificationType: NotificationTypeEnum,
                $isPending: Boolean,
            ) {
              notifications (
                timestamp: $timestamp,
                timestampLte: $timestampLte,
                timestampGte: $timestampGte,
                status: $status,
                notificationType: $notificationType,
                isPending: $isPending,
              ) {
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
        notification_meta = dict(
            project=project,
            receiver=user,
        )
        NotificationFactory.create(
            notification_type=Notification.Type.PROJECT_JOIN_REQUEST,
            status=Notification.Status.UNSEEN,
            timestamp=datetime.datetime(2021, 1, 1, 0, 0, 0, 0, tzinfo=pytz.UTC),
            **notification_meta,
        )
        NotificationFactory.create(
            notification_type=Notification.Type.PROJECT_JOIN_REQUEST,
            status=Notification.Status.SEEN,
            timestamp=datetime.datetime(2021, 1, 10, 0, 0, 0, 0, tzinfo=pytz.UTC),
            **notification_meta,
        )
        NotificationFactory.create(
            notification_type=Notification.Type.PROJECT_JOIN_REQUEST_ABORT,
            status=Notification.Status.UNSEEN,
            timestamp=datetime.datetime(2021, 2, 1, 0, 0, 0, 0, tzinfo=pytz.UTC),
            data={'status': 'pending'},
            **notification_meta,
        )

        def _query_check(filters, **kwargs):
            return self.query_check(query, variables=filters, **kwargs)

        # --- With login
        self.force_login(user)
        for filters, count in [
                ({'status': self.genum(Notification.Status.SEEN)}, 1),
                ({'status': self.genum(Notification.Status.UNSEEN)}, 2),
                ({'notificationType': self.genum(Notification.Type.PROJECT_JOIN_REQUEST)}, 2),
                ({'notificationType': self.genum(Notification.Type.PROJECT_JOIN_REQUEST_ABORT)}, 1),
                ({'isPending': True}, 1),
                ({'isPending': False}, 2),
                ({'timestampGte': '2021-01-01T00:00:00+00:00', 'timestampLte': '2021-01-01T00:00:00+00:00'}, 1),
                ({'timestampGte': '2021-01-01T00:00:00+00:00', 'timestampLte': '2021-02-01T00:00:00+00:00'}, 3),
                ({'timestamp': '2021-01-01T00:00:00+00:00'}, 1),
        ]:
            content = _query_check(filters)
            self.assertEqual(content['data']['notifications']['totalCount'], count, f'\n{filters=} \n{content=}')
            self.assertEqual(len(content['data']['notifications']['results']), count, f'\n{filters=} \n{content=}')


class TestAssignmentQuerySchema(GraphQLTestCase):
    def test_assignments_query(self):
        query = '''
        query MyQuery {
            assignments(isDone: false) {
            results {
              contentData {
                contentType
                entry {
                  id
                }
                lead {
                  id
                  title
                }
              }
              createdAt
              id
              isDone
              objectId
              project {
                id
                title
              }
            }
          }
        }
        '''
        project = ProjectFactory.create()
        user = UserFactory.create()
        lead = LeadFactory.create()
        assignment = AssignmentFactory.create(
            project=project.id,
            object_id=lead.id
        )
