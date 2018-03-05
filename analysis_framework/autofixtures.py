from autofixture import register, generators, create_one, AutoFixture
from .models import AnalysisFramework, Widget, Filter, Exportable


class WidgetAutoFixture(AutoFixture):
    overwrite_defaults = True

    def post_process_instance(self, instance, commit):
        create_one(Filter, overwrite_defaults=True, field_values={
            'analysis_framework': instance.analysis_framework,
            'widget_key': instance.key,
        })

        create_one(Exportable, overwrite_defaults=True, field_values={
            'analysis_framework': instance.analysis_framework,
            'widget_key': instance.key,
        })


class AnalysisFrameworkAutoFixture(AutoFixture):
    overwrite_defaults = True
    field_values = {
        'snapshot_one': None,
        'snapshot_two': None,
    }

    def post_process_instance(self, instance, commit):
        generators.MultipleInstanceGenerator(
            WidgetAutoFixture(Widget, field_values={
                'analysis_framework': instance,
            }),
            min_count=10,
            max_count=20,
        ).generate()


register(Widget, WidgetAutoFixture)
register(AnalysisFramework, AnalysisFrameworkAutoFixture)
