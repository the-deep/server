# from django.utils.functional import cached_property


class GQLContext:
    def __init__(self, request):
        self.request = request

    # FIXME: Is this required here?
    # @cached_property
    @property
    def user(self):
        return self.request.user
