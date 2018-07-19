from django.conf import settings
import requests


RECAPTCHA_URL = 'https://www.google.com/recaptcha/api/siteverify'
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36',  # noqa
}


def validate_recaptcha(recaptcha_response):
    if settings.TESTING:
        return True

    if not (recaptcha_response and settings.RECAPTCHA_SECRET):
        return False

    data = {
        'secret': settings.RECAPTCHA_SECRET,
        'response': recaptcha_response,
    }
    r = requests.post(
        RECAPTCHA_URL,
        data=data,
        headers=HEADERS,
    ).json()

    return r.get('success')
