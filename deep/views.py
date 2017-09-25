import logging
from django.views.generic import View
from django.http import HttpResponse
from django.conf import settings

import os


class FrontendView(View):
    def get(self, request):
        try:
            with open(os.path.join(settings.REACT_APP_DIR,
                                   'build', 'index.html')) as f:
                return HttpResponse(f.read())
        except FileNotFoundError:
            if not settings.TESTING:
                logging.exception('Production build of app not found')
            return HttpResponse(status=404)
