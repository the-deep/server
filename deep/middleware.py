from reversion.views import create_revision


class RevisionMiddleware:
    skip_paths = [
        '/api/v1/token/',
    ]

    def __init__(self, get_response):
        if get_response is not None:
            self.get_response = create_revision()(get_response)
        self.original_get_response = get_response

    def __call__(self, request):
        if request.path in self.skip_paths:
            return self.original_get_response(request)
        return self.get_response(request)
