from collections import defaultdict

from promise import Promise
from django.utils.functional import cached_property

from utils.graphene.dataloaders import DataLoaderWithContext, WithContextMixin

from quality_assurance.models import EntryReviewCommentText


class EntryReviewCommentTextLoader(DataLoaderWithContext):
    def batch_load_fn(self, keys):
        comment_text_qs = EntryReviewCommentText.objects.filter(comment__in=keys)
        comments_text = defaultdict(list)
        for comment_text in comment_text_qs:
            comments_text[comment_text.comment_id].append(comment_text)
        return Promise.resolve([comments_text.get(key) for key in keys])


class DataLoaders(WithContextMixin):

    @cached_property
    def text_history(self):
        return EntryReviewCommentTextLoader(context=self.context)
