from rest_framework import pagination


class ComprehensiveEntriesSetPagination(pagination.LimitOffsetPagination):
    default_limit = 20
    max_limit = 50
