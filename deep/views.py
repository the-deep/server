from rest_framework.exceptions import NotFound
from rest_framework import status
from rest_framework.views import APIView

from django.views.generic import View
from django.http import HttpResponse
from django.conf import settings


class FrontendView(View):
    def get(self, request):
        # TODO: make nice redirect page
        frontend_url = settings.DEEPER_FRONTEND_HOST
        frontend_url = frontend_url if frontend_url is not '*' else\
            'localhost:3000'
        return HttpResponse('THIS IS DEEP API ENDPOINT GOTO: http://' +
                            frontend_url)


class Api_404View(APIView):
    def get(self, request, version):
        raise NotFound(detail="Error 404, page not found",
                       code=status.HTTP_404_NOT_FOUND)
