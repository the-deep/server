import base64
import requests
from django.conf import settings


class KoboToolbox():
    CLIENT_ID = settings.KOBO_TOOLBOX_CLIENT_ID
    CLIENT_SECRET = settings.KOBO_TOOLBOX_CLIENT_SECRET
    REDIRECT_URI = settings.KOBO_TOOLBOX_REDIRECT_URI

    def __init__(self, access_code=None, username=None, password=None):
        self.username = username
        self.password = password
        self.access_token = None

        if access_code:
            if self.CLIENT_ID is None or self.CLIENT_SECRET is None or self.REDIRECT_URI is None:
                raise Exception('KoboToolbox is not configured for Oauth, Contact Admin')

            res = requests.post(
                'https://kf.kobotoolbox.org/o/token/',
                data={
                    'grant_type': 'authorization_code',
                    'client_id': self.CLIENT_ID,
                    'redirect_uri': self.REDIRECT_URI,
                    'code': access_code,
                },
                auth=(self.CLIENT_ID, self.CLIENT_SECRET),
            ).json()
            self.access_token = res['access_token']

    @property
    def auth(self):
        params = {'headers': {'Accept': 'application/json'}}
        if self.access_token:
            params['headers']['Authorization'] = f"Bearer {self.access_token}"
        else:
            params['auth'] = (self.username, self.password)
        return params

    def getEncodedFile(self, file):
        file.seek(0)
        # 'base64,' required by kobo-api https://github.com/kobotoolbox/kpi/blob/3b8a9bb/kpi/views.py#L502
        return b"base64," + base64.b64encode(file.read())

    def export(self, file):
        assest = requests.post('https://kf.kobotoolbox.org/api/v2/assets/', data={
            'name': "Untitled (IMPORTED FROM DEEP)",
            'asset_type': 'survey',
        }, **self.auth).json()

        import_trigger = requests.post(
            'https://kf.kobotoolbox.org/imports/',
            data={
                'totalFiles': 1,
                'destination': assest['url'],
                'assetUid': assest['uid'],
                'name': file.name,
                'base64Encoded': self.getEncodedFile(file),
            },
            **self.auth,
        ).json()

        return {
            'assert_settings': f"https://kf.kobotoolbox.org/#/forms/{assest['uid']}/settings",
            'assert_form': f"https://kf.kobotoolbox.org/#/forms/{assest['uid']}/edit",
            'assert': assest,
            'import': import_trigger,
        }
