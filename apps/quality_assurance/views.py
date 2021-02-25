from rest_framework import (
    viewsets,
    permissions,
)
import django_filters

from deep.permissions import ModifyPermission, IsProjectMember

from .serializers import EntryReviewCommentSerializer
from .models import (
    EntryReviewComment,
)


class EntryReviewCommentViewSet(viewsets.ModelViewSet):
    serializer_class = EntryReviewCommentSerializer
    permission_classes = [permissions.IsAuthenticated, ModifyPermission, IsProjectMember]
    filter_backends = (django_filters.rest_framework.DjangoFilterBackend,)
    # filterset_class = EntryCommentFilterSet

    def get_queryset(self):
        return EntryReviewComment.get_for(self.request.user).filter(entry=self.kwargs['entry_id'])

    def get_serializer_context(self):
        return {
            **super().get_serializer_context(),
            'entry_id': self.kwargs.get('entry_id'),
        }
