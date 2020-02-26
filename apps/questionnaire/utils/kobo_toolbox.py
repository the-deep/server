import base64
import requests


class KoboToolbox():
    def __init__(self, username=None, password=None):
        self.username = username
        self.password = password
        self.access_token = None

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
