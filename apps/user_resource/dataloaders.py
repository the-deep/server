from collections import defaultdict
from promise import Promise
from django.contrib.postgres.aggregates.general import ArrayAgg
from django.utils.functional import cached_property
from django.db.models import F

from utils.graphene.dataloaders import DataLoaderWithContext, WithContextMixin
from user.models import User


def user_batch_load_fn(objs, field):
    objs_by_model = defaultdict(list)
    for obj in objs:
        objs_by_model[type(obj)].append(obj.pk)
    _map = {}
    for model, keys in objs_by_model.items():
        by_qs = User.objects\
            .annotate(related_id=F(f'{model.__name__.lower()}_{field}__pk'))\
            .filter(related_id__in=keys)\
            .annotate(related_ids=ArrayAgg(F('related_id')))
        for user in by_qs.all():
            for related_id in user.related_ids:
                _map[related_id] = user
    return Promise.resolve([_map.get(obj.id) for obj in objs])


class CreatedByLoader(DataLoaderWithContext):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def batch_load_fn(self, objs):
        return user_batch_load_fn(objs, 'created')


class ModifiedByLoader(DataLoaderWithContext):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def batch_load_fn(self, objs):
        return user_batch_load_fn(objs, 'modified')


class DataLoaders(WithContextMixin):
    @cached_property
    def created_by(self):
        return CreatedByLoader(context=self.context)

    @cached_property
    def modified_by(self):
        return ModifiedByLoader(context=self.context)
