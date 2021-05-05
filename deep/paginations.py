from rest_framework import pagination


class AutocompleteSetPagination(pagination.LimitOffsetPagination):
    default_limit = 10
    max_limit = 15


class SmallSizeSetPagination(pagination.LimitOffsetPagination):
    default_limit = 10
    max_limit = 50


class AssignmentPagination(pagination.LimitOffsetPagination):
    default_limit = 5
    max_limit = 10
