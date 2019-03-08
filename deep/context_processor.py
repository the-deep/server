from django.conf import settings


def deep(request):
    return {
        'request': request,
        'DEEP_ENVIRONMENT': settings.DEEP_ENVIRONMENT,
    }
