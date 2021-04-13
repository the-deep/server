from django.conf import settings
from django.contrib.admindocs.views import simplify_regex
from importlib import import_module
from django.urls import (
    URLPattern, URLResolver,
)
from django.urls.resolvers import RoutePattern


def endpoint_ordering(endpoint):
    path, method, callback = endpoint
    method_priority = {
        'GET': 0,
        'POST': 1,
        'PUT': 2,
        'PATCH': 3,
        'DELETE': 4
    }.get(method, 5)

    # Sort first by path then by method
    return (path, method_priority)


class EndpointEnumerator:
    def __init__(self):
        urls = import_module(settings.ROOT_URLCONF)
        patterns = urls.urlpatterns
        self.api_endpoints = self.get_api_endpoints(patterns)

    def get_api_endpoints(self, patterns, prefix=''):
        api_endpoints = []

        for pattern in patterns:
            path_regex = prefix + pattern.pattern.regex.pattern

            if isinstance(pattern.pattern, RoutePattern):
                # TODO: Add fix for RoutePattern
                continue

            if isinstance(pattern, URLPattern):
                path = self.get_path_from_regex(path_regex)
                callback = pattern.callback
                if self.should_include_endpoint(path, callback):
                    for method in self.get_allowed_methods(callback):
                        endpoint = (path, method, callback)
                        api_endpoints.append(endpoint)

            elif isinstance(pattern, URLResolver):
                nested_endpoints = self.get_api_endpoints(
                    patterns=pattern.url_patterns,
                    prefix=path_regex
                )
                api_endpoints.extend(nested_endpoints)

        return sorted(api_endpoints, key=endpoint_ordering)

    def get_path_from_regex(self, path_regex):
        path = simplify_regex(path_regex)
        path = path.replace('<', '{').replace('>', '}')
        return path

    def should_include_endpoint(self, path, callback):
        if not self.is_api_view(callback):
            return False

        if path.endswith('.{format}') or path.endswith('.{format}/'):
            return False

        return True

    def is_api_view(self, callback):
        from rest_framework.views import APIView
        cls = getattr(callback, 'cls', None)
        return cls is not None and issubclass(cls, APIView)

    def get_allowed_methods(self, callback):
        if hasattr(callback, 'actions'):
            actions = set(callback.actions.keys())
            http_method_names = set(callback.cls.http_method_names)
            return [method.upper() for method in actions & http_method_names]

        return [
            method for method in
            callback.cls().allowed_methods if method not in ('OPTIONS', 'HEAD')
        ]
