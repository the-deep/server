from django.conf import settings
import requests

from .errors import InvalidCaptchaError

HCAPTCHA_VERIFY_URL = 'https://hcaptcha.com/siteverify'


def _validate_hcaptcha(captcha):
    if not captcha:
        return False

    data = {
        'secret': settings.HCAPTCHA_SECRET,
        'response': captcha,
    }
    response = requests.post(url=HCAPTCHA_VERIFY_URL, data=data)

    response_json = response.json()
    return response_json['success']


def validate_hcaptcha(captcha, raise_on_error=True):
    is_valid = _validate_hcaptcha(captcha)
    if not is_valid and raise_on_error:
        raise InvalidCaptchaError
    return is_valid
