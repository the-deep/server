from django.conf import settings
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode


def get_private_file_url(obj, id):
    return '{protocol}://{domain}{url}'.format(
        protocol=settings.HTTP_PROTOCOL,
        domain=settings.DJANGO_API_HOST,
        url=reverse(
            'external_private_url',
            kwargs={
                'module': obj,
                'identifier': urlsafe_base64_encode(force_bytes(id))
            }
        )
    )
