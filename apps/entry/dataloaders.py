from collections import defaultdict

from promise import Promise
from django.utils.functional import cached_property
from django.db import models

from utils.graphene.dataloaders import DataLoaderWithContext, WithContextMixin

from .models import (
    Attribute,
    EntryGroupLabel,
)


class EntryAttributesLoader(DataLoaderWithContext):
    def batch_load_fn(self, keys):
        attributes_qs = Attribute.objects.filter(entry__in=keys).annotate(
            widget_type=models.F('widget__widget_id'),
        )
        attributes = defaultdict(list)
        for attribute in attributes_qs:
            attributes[attribute.entry_id].append(attribute)
        return Promise.resolve([attributes.get(key) for key in keys])


class EntryProjectLabelsLoader(DataLoaderWithContext):
    def batch_load_fn(self, keys):
        group_labels_qs = EntryGroupLabel.get_stat_for_entry(
            EntryGroupLabel.objects.filter(entry__in=keys)
        )
        group_labels = defaultdict(list)
        for group_label in group_labels_qs:
            group_labels[group_label['entry']].append(group_label)
        return Promise.resolve([group_labels.get(key) for key in keys])


class DataLoaders(WithContextMixin):
    @cached_property
    def entry_attributes(self):
        return EntryAttributesLoader(context=self.context)

    @cached_property
    def entry_project_labels(self):
        return EntryProjectLabelsLoader(context=self.context)
