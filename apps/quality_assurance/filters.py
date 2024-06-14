import django_filters

from utils.graphene.filters import IDFilter, MultipleInputFilter

from .enums import EntryReviewCommentOrderingEnum
from .models import EntryReviewComment


class EntryReviewCommentGQFilterSet(django_filters.FilterSet):
    entry = IDFilter()
    ordering = MultipleInputFilter(EntryReviewCommentOrderingEnum, method="ordering_filter")

    class Meta:
        model = EntryReviewComment
        fields = ()

    def ordering_filter(self, qs, name, value):
        return qs.order_by(*value)
