from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils.crypto import get_random_string
import logging
import requests

from user.models import Profile

logger = logging.getLogger(__name__)
User = get_user_model()


class HidConfig:
    """
    HID Configs
    """
    def __init__(self):
        self.client_id = settings.HID_CLIENT_ID
        self.redirect_url = settings.HID_CLIENT_REDIRECT_URL
        self.auth_uri = settings.HID_AUTH_URI


config = HidConfig()


class HumanitarianId:
    """
    Handles HID Token
    Login Existing User
    Register New User
    """
    def __init__(self, access_token):
        self.token, self.user_id = self.get_token_and_user_id(access_token)

        if not config.client_id or not self.token or not self.user_id:
            self.status = False
            return

        url = config.auth_uri + '/api/v2/user/' + self.user_id
        r = requests.get(url,
                         headers={'Authorization': 'Bearer ' + self.token})
        # Verify User
        if r.status_code == 200:
            self.data = r.json()
            if self.data['email_verified'] and not self.data['deleted']:
                self.status = True
            else:
                self.status = False
        else:
            self.status = False

    def get_user(self):
        if not self.status:
            return None

        profile = Profile.objects.filter(hid=self.user_id).first()
        if profile is None:
            user = User.objects.filter(email=self.data['email']).first()
            if user:
                self._save_user(user)
            else:
                user = self._create_user()
            return user
        return profile.user

    def _save_user(self, user):
        """
        Sync data from HID to user
        """
        user.first_name = self.data['given_name']
        user.last_name = self.data['family_name']
        user.email = self.data['email']
        user.profile.hid = self.user_id
        user.profile.organization = self.data.get('organization').get('name')\
            if self.data.get('organization')\
            else user.profile.organization

        user.save()

    def _create_user(self):
        """
        Create User with HID data
        """
        username = self.data['email']
        password = get_random_string(length=32)

        user = User.objects.create_user(
            first_name=self.data['given_name'],
            last_name=self.data['family_name'],
            email=self.data['email'],
            username=username,
            password=password
        )

        user.profile.hid = self.user_id
        user.profile.organization = self.data.get('organization').get('name')\
            if self.data.get('organization')\
            else ''

        user.save()
        return user

    def get_token_and_user_id(self, access_token):
        if config.client_id:
            url = config.auth_uri + '/account.json?' \
                'access_token=' + access_token

            r = requests.get(url)
            if r.status_code == 200:
                data = r.json()
                return access_token, data['_id']
            else:
                logger.error(r.json())

        return None, None
