from autofixture import (
    register,
    generators,
    create_one,
    constraints,
    AutoFixture,
)

from .models import Entry, Attribute, FilterData, ExportData
from analysis_framework.models import Filter

import random


def entry_constraint(model, instance):
    if instance.analysis_framework != instance.lead.project.analysis_framework:
        raise constraints.InvalidConstraint([
            model._meta.get_field('lead'),
            model._meta.get_field('analysis_framework'),
        ])


class EntryAutoFixture(AutoFixture):
    overwrite_defaults = True
    default_constraints = [
        constraints.unique_constraint,
        constraints.unique_together_constraint,
        entry_constraint,
    ]

    def post_process_instance(self, instance, commit):
        af = instance.analysis_framework
        for widget in af.widget_set.all():
            create_one(Attribute, overwrite_defaults=True, field_values={
                'widget': widget,
                'entry': instance,
            })

        word_gen = generators.LoremWordGenerator()
        num_gen = generators.IntegerGenerator()

        for filter in af.filter_set.all():
            values = None
            number = None
            if filter.filter_type == Filter.LIST:
                values = [word_gen.generate()
                          for _ in range(random.randint(0, 10))]
            elif filter.filter_type == Filter.NUMBER:
                number = num_gen.generate()

            create_one(FilterData, overwrite_defaults=True, field_values={
                'filter': filter,
                'entry': instance,
                'values': values,
                'number': number,
            })

        for exportable in af.exportable_set.all():
            create_one(ExportData, overwrite_defaults=True, field_values={
                'exportable': exportable,
                'entry': instance,
            })


register(Entry, EntryAutoFixture)
