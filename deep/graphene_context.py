class GQLContext:
    def __init__(self, request):
        self.request = request

    @property
    def user(self):
        return self.request.user
