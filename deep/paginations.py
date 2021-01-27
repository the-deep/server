from rest_framework import pagination


class AutocompleteSetPagination(pagination.LimitOffsetPagination):
    default_limit = 10
    max_limit = 15


class SmallSizeSetPagination(pagination.LimitOffsetPagination):
    default_limit = 10
    max_limit = 25
