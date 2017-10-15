from django.http import HttpResponse
from django.template.loader import render_to_string
from django.views.generic import View

from .schema_generator import SchemaGenerator

import json


class DocsView(View):
    def get(self, request, version=None):
        context = {}
        endpoints = []

        for key, endpoint in SchemaGenerator().links.items():
            endpoints.append((key, [
                (key, e) for (key, e) in endpoint.items()
                if isinstance(e, dict)
            ]))

        context['endpoints'] = endpoints
        return HttpResponse(
            json.dumps(
                json.loads(
                    render_to_string('docs/index.html', context)
                ),
            ),
            content_type='application/json',
        )
