from utils.graphene.tests import GraphQLTestCase

from user.factories import UserFactory
from notification.factories import NotificationFactory
from notification.models import Notification


class NotificationMutation(GraphQLTestCase):
    def test_notification_status_update(self):
        self.notification_query = '''
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
        '''

        user = UserFactory.create()
        notification = NotificationFactory.create(status=Notification.Status.UNSEEN, receiver=user)

        def _query_check(minput, **kwargs):
            return self.query_check(
                self.notification_query,
                minput=minput,
                **kwargs
            )

        minput = dict(id=notification.id, status=self.genum(Notification.Status.SEEN))
        # -- Without login
        _query_check(minput, assert_for_error=True)

        # -- With login
        self.force_login(user)
        content = _query_check(minput)
        self.assertEqual(content['data']['notificationStatusUpdate']['errors'], None, content)

        # check for the notification status update(db-level)
        notification = Notification.objects.get(id=notification.id)
        assert notification.status == Notification.Status.SEEN
