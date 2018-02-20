from rest_framework.exceptions import NotFound
from rest_framework import status
from rest_framework.views import APIView

from django.views.generic import View
from django.conf import settings
from django.template.response import TemplateResponse


def get_frontend_url(path=''):
    return '{protocol}://{domain}/{path}'.format(
        protocol=settings.HTTP_PROTOCOL or 'http',
        domain=settings.DEEPER_FRONTEND_HOST or 'localhost:3000',
        path=path,
    )


class FrontendView(View):
    def get(self, request):
        # TODO: make nice redirect page
        context = {
            'frontend_url': get_frontend_url(),
        }
        return TemplateResponse(request, 'home/welcome.html', context)


class Api_404View(APIView):
    def get(self, request, version):
        raise NotFound(detail="Error 404, page not found",
                       code=status.HTTP_404_NOT_FOUND)
