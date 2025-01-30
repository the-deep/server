from collections import defaultdict
from promise import Promise

from django.utils.functional import cached_property

from assisted_tagging.models import AssistedTaggingPrediction, LLMAssistedTaggingPredication

from utils.graphene.dataloaders import DataLoaderWithContext, WithContextMixin


class DraftEntryPredicationsLoader(DataLoaderWithContext):
    def batch_load_fn(self, keys):
        assisted_tagging_qs = AssistedTaggingPrediction.objects\
            .filter(draft_entry_id__in=keys, is_selected=True)
        _map = defaultdict(list)
        for assisted_tagging in assisted_tagging_qs:
            _map[assisted_tagging.draft_entry_id].append(assisted_tagging)
        return Promise.resolve([_map.get(key, []) for key in keys])


class LLMDraftEntryPredicationsLoader(DataLoaderWithContext):
    def batch_load_fn(self, keys):
        llm_assisted_tagging_qs = LLMAssistedTaggingPredication.objects.filter(draft_entry_id__in=keys)
        _map = {
            assisted_tagging.draft_entry_id: assisted_tagging
            for assisted_tagging in llm_assisted_tagging_qs
        }
        return Promise.resolve([_map.get(key) for key in keys])


class DataLoaders(WithContextMixin):
    @cached_property
    def draft_entry_predications(self):
        return DraftEntryPredicationsLoader(context=self.context)

    @cached_property
    def llm_draft_entry_predications(self):
        return LLMDraftEntryPredicationsLoader(context=self.context)
