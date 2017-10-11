from django.views.generic import View
from django.shortcuts import render
from .registrar import registered_views

import inspect

class DummyObject:
    pass


class DocsView(View):
    def get(self, request, version):
        context = {}

        views = []
        for view in registered_views:
            view_data = DummyObject()
            view_data.data = inspect.getmembers(view),
            views.append(view_data)

        context['views'] = views
        return render(request, 'docs/index.html', context)
