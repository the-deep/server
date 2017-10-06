from rest_framework import status
from django.test import TestCase
from utils.hid import config as hid_config
from utils.common import USER_AGENT
from urllib.parse import urlparse
import requests
import logging

from utils.hid import HumanitarianId
from utils.hid.hid import User

# NOTE: Make sure this works for testing
# NOTE: Also add deep app to this user in HID
HID_EMAIL = 'dev@togglecorp.com'
HID_PASSWORD = '.(tTdCh7NnP9K=)T'
HID_FIRSTNAME = 'Togglecorp'
HID_LASTNAME = 'Dev'

# TODO: use redirect_uri from django config
HID_LOGIN_URL = hid_config.auth_uri + '/oauth/authorize?'\
    'response_type=token&client_id=' + hid_config.client_id +\
    '&scope=profile&state=12345&'\
    'redirect_uri=' + hid_config.redirect_url

logger = logging.getLogger(__name__)


class HIDIntegrationTest(TestCase):
    """
    Test HID Integration
    """
    def setUp(self):
        self.requests = requests.session()
        self.headers = {
            'User-Agent': USER_AGENT
        }

    def show_auth_warning(self, response=None, no_access_token=False):
        border_len = 50
        logger.warning('*' * border_len)
        logger.warning('---- HID AUTHS/Config are not working ----')
        logger.warning('HID AUTH URL: ' + HID_LOGIN_URL)
        if response is not None:
            logger.warning('Response Code: ' + str(response.status_code))
            logger.warning('Response Text: ' + str(response.content))
        if no_access_token:
            logger.warning('Got No Access Token From HID')
        logger.warning('*' * border_len)

    def get_access_token(self):
        """
        Get access token from HID
        """
        response = self.requests.get(hid_config.auth_uri, headers=self.headers)
        response = self.requests.post(
            hid_config.auth_uri + '/login',
            data={
                'email': HID_EMAIL,
                'password': HID_PASSWORD,
                'crumb': response.cookies.get('crumb'),
            },
            headers=self.headers)
        response = self.requests.get(HID_LOGIN_URL, headers=self.headers)

        if response.status_code == status.HTTP_403_FORBIDDEN\
                or len(response.history) < 1:
            self.show_auth_warning(response=response)
            return

        redirect_url = response.history[0].headers.get('location')
        p = urlparse(redirect_url.replace('#', '?', 1))
        access_token = {query.split('=')[0]: query.split('=')[1]
                        for query in p.query.split('&')}.get('access_token')
        if access_token is None:
            self.show_auth_warning(response=response, no_access_token=True)
        return access_token

    def test_new_user(self):
        """
        Test for new user
        """
        access_token = self.get_access_token()
        # NOTE: To avoid error on auth fail
        if access_token is None:
            return
        user = HumanitarianId(access_token).get_user()
        self.assertEqual(user.email, HID_EMAIL)
        user.delete()

    def test_link_user(self):
        """
        Test for old user
        """

        access_token = self.get_access_token()
        # NOTE: To avoid error on auth fail
        if access_token is None:
            return

        user = User.objects.create_user(
            first_name=HID_FIRSTNAME,
            last_name=HID_LASTNAME,
            email=HID_EMAIL,
            username=HID_EMAIL,
            password=HID_PASSWORD
        )

        hid_user = HumanitarianId(access_token).get_user()
        self.assertEqual(hid_user, user)
        user.delete()
