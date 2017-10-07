from django.views.generic import View
from django.http import HttpResponse
from django.conf import settings


class FrontendView(View):
    def get(self, request):
        frontend_url = settings.ALLOWED_HOSTS[0]
        frontend_url = frontend_url if frontend_url is not '*' else\
            'localhost:3000'
        return HttpResponse('THIS IS DEEP API ENDPOINT GOTO: http://' +
                            frontend_url)
