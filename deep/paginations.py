from rest_framework import pagination


class HardLimitSetPagination(pagination.LimitOffsetPagination):
    default_limit = 20
    max_limit = 100


class AutocompleteSetPagination(HardLimitSetPagination):
    default_limit = 10
    max_limit = 15
