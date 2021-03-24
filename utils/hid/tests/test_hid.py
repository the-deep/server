import requests
import logging

from mock import patch

# from rest_framework import status
from django.test import TestCase
from utils.hid import hid
from utils.common import DEFAULT_HEADERS

# from urllib.parse import urlparse
# from requests.exceptions import ConnectionError
# import traceback

# MOCK Data
HID_EMAIL = 'dev@togglecorp.com'
HID_PASSWORD = 'XXXXXXXXXXXXXXXX'
HID_FIRSTNAME = 'Togglecorp'
HID_LASTNAME = 'Dev'

HID_LOGIN_URL = (
    f'{hid.config.auth_uri}/oauth/authorize?'
    f'response_type=token&client_id={hid.config.client_id}&scope=profile&state=12345&redirect_uri={hid.config.redirect_url}'
)

logger = logging.getLogger(__name__)


class HIDIntegrationTest(TestCase):
    """
    Test HID Integration
    """
    def setUp(self):
        self.requests = requests.session()
        self.headers = DEFAULT_HEADERS

    """
    # NOTE: NOT USED ANYMORE. LEAVING IT HERE FOR REFERENCE ONLY #####
    def show_auth_warning(self, response=None, no_access_token=False,
                          message=None):
        border_len = 50
        logger.warning('*' * border_len)
        logger.warning('---- HID AUTHS/Config are not working ----')
        logger.warning('HID AUTH URL: ' + HID_LOGIN_URL)
        if response is not None:
            logger.warning('Response Code: ' + str(response.status_code))
            logger.warning('Response Text: ' + str(response.content))
        if no_access_token:
            logger.warning('Got No Access Token From HID')
        if message:
            logger.warning(message)
        logger.warning('*' * border_len)
    """

    def get_access_token(self):
        """
        Get access token from HID
        """
        # Mocking
        return 'XXXXXXXXXXXXXXXXXXXXXXXXXXXX'
        """
        # NOTE: LIVE API IS NOT USED FOR TESTING. LEAVING IT HERE FOR REFERENCE ONLY #####

        # Send request to get crumb cookie, required for login.
        response = self.requests.get(hid.config.auth_uri, headers=self.headers)

        # Try to login with dev user
        response = self.requests.post(
            hid.config.auth_uri + '/login',
            data={
                'email': HID_EMAIL,
                'password': HID_PASSWORD,
                'crumb': response.cookies.get('crumb'),
            },
            headers=self.headers)

        try:
            # Now try to get callback user.
            response = self.requests.get(HID_LOGIN_URL, headers=self.headers)

            if response.status_code == status.HTTP_403_FORBIDDEN\
                    or len(response.history) < 1:
                self.show_auth_warning(response=response)
                return

            redirect_url = response.history[0].headers.get('location')
        except ConnectionError as response:
            # get the final url where we get timeout, since the callback is
            # into react container 3000 instead of django 8000
            redirect_url = response.request.url

        p = urlparse(redirect_url.replace('#', '?', 1))
        access_token = {query.split('=')[0]: query.split('=')[1]
                        for query in p.query.split('&')}.get('access_token')

        if access_token is None:
            self.show_auth_warning(response=response, no_access_token=True)
        return access_token
        """

    def _setup_mock_hid_requests(self, mock_requests):
        # post -> /account.json
        mock_requests.post.return_value.status_code = 200
        mock_requests.post.return_value.json.return_value = {
            # Also returns other value, but we don't require it for now
            'id': 'xxxxxxx1234xxxxxxxxxxxx',
            'sub': 'xxxxxxx1234xxxxxxxxxxxx',
            # Also returns other value, but we don't require it for now
            "email_verified": True,
            "email": HID_EMAIL,
            "name": "Xxxxxx Xxxxxx",
            "given_name": "Xxxxxx",
            "family_name": "Xxxxxx",
            # NOTE USED
            "iss": "https://auth.humanitarian.id",
            "user_id": "",
        }
        return mock_requests.post.return_value

    @patch('utils.hid.hid.requests')
    def test_new_user(self, mock_requests):
        """
        Test for new user
        """
        mock_return_value = self._setup_mock_hid_requests(mock_requests)
        access_token = self.get_access_token()
        user = hid.HumanitarianId(access_token).get_user()
        self.assertEqual(getattr(user, 'email', None), HID_EMAIL)
        user.delete()

        mock_return_value.status_code = 400
        with self.assertRaises(hid.HIDFetchFailedException):
            user = hid.HumanitarianId(access_token).get_user()
        mock_return_value.status_code = 200

        mock_return_value.json.return_value['email_verified'] = False
        with self.assertRaises(hid.HIDEmailNotVerifiedException):
            user = hid.HumanitarianId(access_token).get_user()
        mock_return_value.json.return_value['email_verified'] = True

        mock_return_value.json.return_value.pop('given_name')
        with self.assertRaises(KeyError):
            user = hid.HumanitarianId(access_token).get_user()
        mock_return_value.json.return_value['given_name'] = 'Xxxxxx'

    @patch('utils.hid.hid.requests')
    def test_link_user(self, mock_requests):
        """
        Test for old user
        """

        self._setup_mock_hid_requests(mock_requests)
        access_token = self.get_access_token()

        user = hid.User.objects.create_user(
            first_name=HID_FIRSTNAME,
            last_name=HID_LASTNAME,
            email=HID_EMAIL,
            username=HID_EMAIL,
            password=HID_PASSWORD
        )

        hid_user = hid.HumanitarianId(access_token).get_user()
        self.assertEqual(hid_user, user)
        user.delete()
