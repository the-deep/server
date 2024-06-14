from collections import defaultdict

from analysis_framework.models import Widget
from django.db import models
from django.utils.functional import cached_property
from geo.schema import get_geo_area_queryset_for_project_geo_area_type
from promise import Promise
from quality_assurance.models import EntryReviewComment

from utils.graphene.dataloaders import DataLoaderWithContext, WithContextMixin

from .models import Attribute, Entry, EntryGroupLabel


class EntryLoader(DataLoaderWithContext):
    def batch_load_fn(self, keys):
        entry_qs = Entry.objects.filter(id__in=keys)
        _map = {entry.id: entry for entry in entry_qs}
        return Promise.resolve([_map[key] for key in keys])


class EntryAttributesLoader(DataLoaderWithContext):
    def batch_load_fn(self, keys):
        attributes_qs = (
            Attribute.objects.filter(entry__in=keys)
            .exclude(widget__widget_id__in=Widget.DEPRECATED_TYPES)
            .annotate(widget_type=models.F("widget__widget_id"))
        )
        attributes = defaultdict(list)
        for attribute in attributes_qs:
            attributes[attribute.entry_id].append(attribute)
        return Promise.resolve([attributes.get(key) for key in keys])


class EntryProjectLabelsLoader(DataLoaderWithContext):
    def batch_load_fn(self, keys):
        group_labels_qs = EntryGroupLabel.get_stat_for_entry(EntryGroupLabel.objects.filter(entry__in=keys))
        group_labels = defaultdict(list)
        for group_label in group_labels_qs:
            group_labels[group_label["entry"]].append(group_label)
        return Promise.resolve([group_labels.get(key) for key in keys])


class AttributeGeoSelectedOptionsLoader(DataLoaderWithContext):
    def batch_load_fn(self, keys):
        geo_area_qs = (
            get_geo_area_queryset_for_project_geo_area_type().filter(id__in={id for ids in keys for id in ids}).defer("polygons")
        )
        geo_area_map = {str(geo_area.id): geo_area for geo_area in geo_area_qs}
        return Promise.resolve([[geo_area_map[str(id)] for id in ids if id in geo_area_map] for ids in keys])


class ReviewCommentsLoader(DataLoaderWithContext):
    def batch_load_fn(self, keys):
        comment_qs = EntryReviewComment.objects.filter(entry__in=keys)
        comments = defaultdict(list)
        for comment in comment_qs:
            comments[comment.entry_id].append(comment)
        return Promise.resolve([comments.get(key) for key in keys])


class ReviewCommentsCountLoader(DataLoaderWithContext):
    def batch_load_fn(self, keys):
        count_qs = (
            EntryReviewComment.objects.filter(entry__in=keys)
            .order_by()
            .values("entry")
            .annotate(count=models.Count("id"))
            .values_list("entry", "count")
        )
        counts = {entry_id: count for entry_id, count in count_qs}
        return Promise.resolve([counts.get(key, 0) for key in keys])


class EntryVerifiedByLoader(DataLoaderWithContext):
    def batch_load_fn(self, keys):
        verified_by_through_qs = Entry.verified_by.through.objects.filter(entry__in=keys).prefetch_related("user")
        _map = defaultdict(list)
        for item in verified_by_through_qs.all():
            _map[item.entry_id].append(item.user)
        return Promise.resolve([_map.get(key, []) for key in keys])


class EntryVerifiedByCountLoader(DataLoaderWithContext):
    def batch_load_fn(self, keys):
        count_qs = (
            Entry.verified_by.through.objects.filter(entry__in=keys)
            .order_by()
            .values("entry")
            .annotate(count=models.Count("id"))
            .values_list("entry", "count")
        )
        counts = {entry: count for entry, count in count_qs}
        return Promise.resolve([counts.get(key, 0) for key in keys])


class DataLoaders(WithContextMixin):
    @cached_property
    def entry(self):
        return EntryLoader(context=self.context)

    @cached_property
    def entry_attributes(self):
        return EntryAttributesLoader(context=self.context)

    @cached_property
    def entry_project_labels(self):
        return EntryProjectLabelsLoader(context=self.context)

    @cached_property
    def attribute_geo_selected_options(self):
        return AttributeGeoSelectedOptionsLoader(context=self.context)

    @cached_property
    def review_comments(self):
        return ReviewCommentsLoader(context=self.context)

    @cached_property
    def review_comments_count(self):
        return ReviewCommentsCountLoader(context=self.context)

    @cached_property
    def verified_by(self):
        return EntryVerifiedByLoader(context=self.context)

    @cached_property
    def verified_by_count(self):
        return EntryVerifiedByCountLoader(context=self.context)
