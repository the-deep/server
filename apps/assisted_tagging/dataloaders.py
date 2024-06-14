from collections import defaultdict

from assisted_tagging.models import AssistedTaggingPrediction
from django.utils.functional import cached_property
from promise import Promise

from utils.graphene.dataloaders import DataLoaderWithContext, WithContextMixin


class DraftEntryPredicationsLoader(DataLoaderWithContext):
    def batch_load_fn(self, keys):
        assisted_tagging_qs = AssistedTaggingPrediction.objects.filter(draft_entry_id__in=keys, is_selected=True)
        _map = defaultdict(list)
        for assisted_tagging in assisted_tagging_qs:
            _map[assisted_tagging.draft_entry_id].append(assisted_tagging)
        return Promise.resolve([_map.get(key, []) for key in keys])


class DataLoaders(WithContextMixin):
    @cached_property
    def draft_entry_predications(self):
        return DraftEntryPredicationsLoader(context=self.context)
