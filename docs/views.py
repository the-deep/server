from django.shortcuts import render
from django.views.generic import View

from .schema_generator import SchemaGenerator


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
        return render(request, 'docs/index.html', context)
