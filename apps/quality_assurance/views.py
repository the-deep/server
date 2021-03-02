from rest_framework import (
    mixins,
    permissions,
    response,
    viewsets,
)
import django_filters

from deep.paginations import SmallSizeSetPagination
from deep.permissions import ModifyPermission, IsProjectMember
from entry.models import Entry

from .serializers import (
    EntryReviewCommentSerializer,
    ApprovedBySerializer,
)
from .models import (
    EntryReviewComment,
)


class EntryReviewCommentViewSet(
        mixins.CreateModelMixin,
        mixins.RetrieveModelMixin,
        mixins.ListModelMixin,
        mixins.UpdateModelMixin,
        viewsets.GenericViewSet,
):
    serializer_class = EntryReviewCommentSerializer
    permission_classes = [permissions.IsAuthenticated, ModifyPermission, IsProjectMember]
    filter_backends = (django_filters.rest_framework.DjangoFilterBackend,)
    pagination_class = SmallSizeSetPagination

    def get_queryset(self):
        return EntryReviewComment.get_for(self.request.user).filter(entry=self.kwargs['entry_id'])

    def get_serializer_context(self):
        return {
            **super().get_serializer_context(),
            'entry_id': self.kwargs.get('entry_id'),
        }

    def get_paginated_response(self, data):
        entry = Entry.objects.get(pk=self.kwargs['entry_id'])
        summary_data = {
            'approved_by': ApprovedBySerializer(entry.approved_by.all(), many=True).data,
            'verified': entry.verified,
            'verification_last_changed_by': ApprovedBySerializer(entry.verification_last_changed_by).data,
        }
        return response.Response({
            **super().get_paginated_response(data).data,
            'summary': summary_data,
        })
