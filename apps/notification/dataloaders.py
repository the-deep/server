from django.utils.functional import cached_property

from promise import Promise

from entry.models import EntryComment
from notification.models import Assignment
from lead.models import Lead
from quality_assurance.models import EntryReviewComment

from utils.graphene.dataloaders import DataLoaderWithContext, WithContextMixin


class AssignmentLoader(DataLoaderWithContext):
    def batch_load_fn(self, keys):
        assignment_qs = list(
            Assignment.objects
            .filter(id__in=keys)
            .values_list('id', 'content_type__model', 'object_id')
        )

        leads_id = []
        entry_review_comment_id = []

        for _, content_type, object_id in assignment_qs:
            # TODO use dict map function
            if content_type == Lead._meta.model_name:
                leads_id.append(object_id)
            elif content_type == EntryReviewComment._meta.model_name:
                entry_review_comment_id.append(object_id)

        _lead_id_map = {}

        for _id, title in Lead.objects.filter(id__in=leads_id).values_list('id', 'title'):
            _lead_id_map[_id] = dict(
                id=_id,
                title=title
            )

        _entry_review_comment_id_map = {}

        for _id, text, entry_id, entry_excerpt, lead_id in EntryReviewComment.objects.filter(
            id__in=entry_review_comment_id).values_list(
                'id',
                'comment_texts__text',
                'entry__id',
                'entry__excerpt',
                'entry__lead_id'
        ):
            _entry_review_comment_id_map[_id] = dict(
                id=_id,
                text=text,
                entry_id=entry_id,
                entry_excerpt=entry_excerpt,
                lead_id=lead_id
            )

        _result = {
            _id: {
                'content_type': content_type,
                'lead': _lead_id_map.get(object_id) if content_type == 'lead' else None,
                'entry_review_comment': _entry_review_comment_id_map.get(object_id) if content_type == 'entryreviewcomment' else None,
            }
            for _id, content_type, object_id in assignment_qs
        }
        return Promise.resolve([_result[key] for key in keys])


class DataLoaders(WithContextMixin):
    @cached_property
    def assignment(self):
        return AssignmentLoader(context=self.context)
