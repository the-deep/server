# -*- coding: utf-8 -*-
# SOURCE: https://raw.githubusercontent.com/beda-software/drf-writable-nested/f32ad59/drf_writable_nested/mixins.py
from collections import OrderedDict, defaultdict

from django.contrib.contenttypes.fields import GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.db.models import ProtectedError
from django.core.exceptions import FieldDoesNotExist
from django.db.models.fields.related import ForeignObjectRel
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers


class ListToDictField(serializers.Field):
    """
    Represent a list of entities as a dictionary
    """
    def __init__(self, *args, **kwargs):
        self.child = kwargs.pop('child')
        self.key = kwargs.pop('key')

        assert self.child.source is None, (
            'The `source` argument is not meaningful when '
            'applied to a `child=` field. '
            'Remove `source=` from the field declaration.'
        )

        super().__init__(*args, **kwargs)

    def to_representation(self, obj):
        list_data = self.child.to_representation(obj)
        data = {}

        for item in list_data:
            key_value = item.pop(self.key)
            data[str(key_value)] = item
        return data

    def to_internal_value(self, data):
        list_data = self.to_list_data(data)
        return self.child.run_validation(list_data)

    def to_list_data(self, data):
        list_data = []
        for key, value in data.items():
            list_data.append({
                self.key: key,
                **value,
            })
        return list_data


class BaseNestedModelSerializer(serializers.ModelSerializer):
    def _extract_relations(self, validated_data):
        reverse_relations = OrderedDict()
        relations = OrderedDict()

        # Remove related fields from validated data for future manipulations
        for field_name, field in self.fields.items():
            if field.read_only:
                continue
            try:
                related_field, direct = self._get_related_field(field)
            except FieldDoesNotExist:
                continue

            if isinstance(field, ListToDictField):
                if field.source not in validated_data:
                    # Skip field if field is not required
                    continue

                validated_data.pop(field.source)
                reverse_relations[field_name] = (
                    related_field, field, field.source
                )

            if isinstance(field, serializers.ListSerializer) and \
                    isinstance(field.child, serializers.ModelSerializer):
                if field.source not in validated_data:
                    # Skip field if field is not required
                    continue

                validated_data.pop(field.source)
                reverse_relations[field_name] = (
                    related_field, field.child, field.source
                )

            if isinstance(field, serializers.ModelSerializer):
                if field.source not in validated_data:
                    # Skip field if field is not required
                    continue

                if validated_data.get(field.source) is None:
                    if direct:
                        # Don't process null value for direct relations
                        # Native create/update processes these values
                        continue

                validated_data.pop(field.source)
                # Reversed one-to-one looks like direct foreign keys but they
                # are reverse relations
                if direct:
                    relations[field_name] = (field, field.source)
                else:
                    reverse_relations[field_name] = (
                        related_field, field, field.source)
        return relations, reverse_relations

    def _get_related_field(self, field):
        model_class = self.Meta.model

        if field.source.endswith('_set'):
            related_field = model_class._meta.get_field(field.source[:-4])
        else:
            related_field = model_class._meta.get_field(field.source)

        if isinstance(related_field, ForeignObjectRel):
            return related_field.field, False
        return related_field, True

    def _get_serializer_for_field(self, field, **kwargs):
        kwargs.update({
            'context': self.context,
            'partial': self.partial,
        })
        return field.__class__(**kwargs)

    def _get_generic_lookup(self, instance, related_field):
        return {
            related_field.content_type_field_name:
                ContentType.objects.get_for_model(instance),
            related_field.object_id_field_name: instance.pk,
        }

    def prefetch_related_instances(self, field, related_data):
        model_class = field.Meta.model
        pk_list = []
        for d in filter(None, related_data):
            pk = self._get_related_pk(d, model_class)
            if pk:
                pk_list.append(pk)

        instances = {
            str(related_instance.pk): related_instance
            for related_instance in model_class.objects.filter(
                pk__in=pk_list
            )
        }

        return instances

    def _get_related_pk(self, data, model_class):
        pk = data.get('pk') or data.get(model_class._meta.pk.attname)
        if pk:
            return str(pk)

        return None

    def update_or_create_reverse_relations(self, instance, reverse_relations):
        # Update or create reverse relations:
        # many-to-one, many-to-many, reversed one-to-one
        for field_name, (related_field, field, field_source) in \
                reverse_relations.items():
            related_data = self.initial_data[field_name]
            # Expand to array of one item for one-to-one for uniformity
            if related_field.one_to_one:
                if related_data is None:
                    # Skip processing for empty data
                    continue
                related_data = [related_data]

            if isinstance(field, ListToDictField):
                related_data = field.to_list_data(related_data)
                field = field.child.child

            instances = self.prefetch_related_instances(field, related_data)

            save_kwargs = self.get_save_kwargs(field_name)
            if isinstance(related_field, GenericRelation):
                save_kwargs.update(
                    self._get_generic_lookup(instance, related_field),
                )
            elif not related_field.many_to_many:
                save_kwargs[related_field.name] = instance

            new_related_instances = []
            for data in related_data:
                obj = instances.get(
                    self._get_related_pk(data, field.Meta.model)
                )
                serializer = self._get_serializer_for_field(
                    field,
                    instance=obj,
                    data=data,
                )
                serializer.is_valid(raise_exception=True)
                related_instance = serializer.save(**save_kwargs)
                data['pk'] = related_instance.pk
                new_related_instances.append(related_instance)

            if related_field.many_to_many:
                # Add m2m instances to through model via add
                m2m_manager = getattr(instance, field_source)
                m2m_manager.add(*new_related_instances)

    def update_or_create_direct_relations(self, attrs, relations):
        for field_name, (field, field_source) in relations.items():
            obj = None
            data = self.initial_data[field_name]
            model_class = field.Meta.model
            pk = self._get_related_pk(data, model_class)
            if pk:
                obj = model_class.objects.filter(
                    pk=pk,
                ).first()
            serializer = self._get_serializer_for_field(
                field,
                instance=obj,
                data=data,
            )
            serializer.is_valid(raise_exception=True)
            attrs[field_source] = serializer.save(
                **self.get_save_kwargs(field_name)
            )

    def save(self, **kwargs):
        self.save_kwargs = defaultdict(dict, kwargs)

        return super().save(**kwargs)

    def get_save_kwargs(self, field_name):
        save_kwargs = self.save_kwargs[field_name]
        if not isinstance(save_kwargs, dict):
            raise TypeError(
                _("Arguments to nested serializer's `save` must be dict's")
            )

        return save_kwargs

    def _extract_related_pks(self, field, related_data):
        model_class = field.Meta.model
        pk_list = []
        for d in filter(None, related_data):
            pk = self._get_related_pk(d, model_class)
            if pk:
                pk_list.append(pk)

        return pk_list


class NestedCreateMixin(BaseNestedModelSerializer):
    """
    Mixin adds nested create feature
    """
    def create(self, validated_data):
        relations, reverse_relations = self._extract_relations(validated_data)

        # Create or update direct relations (foreign key, one-to-one)
        self.update_or_create_direct_relations(
            validated_data,
            relations,
        )

        # Create instance
        instance = super().create(validated_data)

        self.update_or_create_reverse_relations(instance, reverse_relations)

        return instance


class NestedUpdateMixin(BaseNestedModelSerializer):
    """
    Mixin adds update nested feature
    """
    default_error_messages = {
        'cannot_delete_protected': _(
            "Cannot delete {instances} because "
            "protected relation exists")
    }

    def update(self, instance, validated_data):
        relations, reverse_relations = self._extract_relations(validated_data)

        # Create or update direct relations (foreign key, one-to-one)
        self.update_or_create_direct_relations(
            validated_data,
            relations,
        )

        # Update instance
        instance = super().update(
            instance,
            validated_data,
        )
        self.delete_reverse_relations_if_need(instance, reverse_relations)
        self.update_or_create_reverse_relations(instance, reverse_relations)
        return instance

    def delete_reverse_relations_if_need(self, instance, reverse_relations):
        # Reverse `reverse_relations` for correct delete priority
        reverse_relations = OrderedDict(
            reversed(list(reverse_relations.items())))

        # Delete instances which is missed in data
        for field_name, (related_field, field, field_source) in \
                reverse_relations.items():
            # related_data = self.initial_data[field_name]
            related_data = self.get_initial()[field_name]

            if isinstance(field, ListToDictField):
                related_data = field.to_list_data(related_data)
                field = field.child.child

            model_class = field.Meta.model
            # Expand to array of one item for one-to-one for uniformity
            if related_field.one_to_one:
                related_data = [related_data]

            # M2M relation can be as direct or as reverse. For direct relation
            # we should use reverse relation name
            if related_field.many_to_many and \
                    not isinstance(related_field, ForeignObjectRel):
                related_field_lookup = {
                    related_field.remote_field.name: instance,
                }
            elif isinstance(related_field, GenericRelation):
                related_field_lookup = \
                    self._get_generic_lookup(instance, related_field)
            else:
                related_field_lookup = {
                    related_field.name: instance,
                }

            # current_ids = [d.get('pk') for d in related_data if d is not None]
            current_ids = self._extract_related_pks(field, related_data)

            try:
                pks_to_delete = list(
                    model_class.objects.filter(
                        **related_field_lookup
                    ).exclude(
                        pk__in=current_ids
                    ).values_list('pk', flat=True)
                )

                if related_field.many_to_many:
                    # Remove relations from m2m table
                    m2m_manager = getattr(instance, field_source)
                    m2m_manager.remove(*pks_to_delete)
                else:
                    model_class.objects.filter(pk__in=pks_to_delete).delete()

            except ProtectedError as e:
                instances = e.args[1]
                self.fail('cannot_delete_protected', instances=", ".join([
                    str(instance) for instance in instances]))
