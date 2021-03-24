from django.conf import settings
from django.contrib.auth import get_user_model
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


class HIDBaseException(Exception):
    def __init__(self, message=None):
        if message:
            self.message = message


class InvalidHIDConfigurationException(HIDBaseException):
    message = 'Invalid HID Configuration'


class HIDFetchFailedException(HIDBaseException):
    message = 'HID User data fetch failed'


class HIDEmailNotVerifiedException(HIDBaseException):
    message = 'Email is not verified in HID'


class HumanitarianId:
    """
    Handles HID Token
    """
    def __init__(self, access_token):
        self.data = self.get_user_information_from_access_token(access_token)
        self.user_id = self.data['sub']

    def get_user(self):
        profile = Profile.objects.filter(hid=self.user_id).first()
        if profile is None:
            user = User.objects.filter(email=self.data['email']).first()
            if user:
                self._save_user(user)
                return user
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
        user.save()

    def _create_user(self):
        """
        Create User with HID data
        """
        username = self.data['email']

        user = User.objects.create_user(
            first_name=self.data['given_name'],
            last_name=self.data['family_name'],
            email=self.data['email'],
            username=username,
        )

        user.profile.hid = self.user_id
        user.save()
        return user

    def get_user_information_from_access_token(self, access_token):
        if config.auth_uri:
            # https://github.com/UN-OCHA/hid_api/blob/363f5a06fe25360515494bce050a6d2987058a2a/api/controllers/UserController.js#L1536-L1546
            url = config.auth_uri + '/account.json'
            r = requests.post(
                url, headers={'Authorization': 'Bearer ' + access_token},
            )
            if r.status_code == 200:
                data = r.json()
                if not data['email_verified']:
                    raise HIDEmailNotVerifiedException()
                return data
            raise HIDFetchFailedException('HID Get Token Failed!! \n{}'.format(r.json()))
        raise InvalidHIDConfigurationException()
