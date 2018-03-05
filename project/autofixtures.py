from django.contrib.auth.models import User
from autofixture import register, generators, AutoFixture

from .models import Project, ProjectMembership
from geo.models import Region
from analysis_framework.models import AnalysisFramework

from geo.autofixtures import RegionAutoFixture
from analysis_framework.autofixtures import AnalysisFrameworkAutoFixture

import random


class ProjectAutoFixture(AutoFixture):
    overwrite_defaults = True
    field_values = {
        'assessment_template': None,
        'category_editor': None,
        'analysis_framework': AnalysisFrameworkAutoFixture(AnalysisFramework),
    }
    follow_m2m = {
        'user_groups': (1, 1),
    }

    def post_process_instance(self, instance, commit):
        groups = instance.user_groups.all()
        valid_members = User.objects.exclude(
            usergroup__in=groups,
        )
        generators.MultipleInstanceGenerator(
            AutoFixture(ProjectMembership, field_values={
                'project': instance,
                'member': generators.InstanceSelector(valid_members),
            }, ),
            min_count=1,
            max_count=2,
        ).generate()

        region_generator = generators.WeightedGenerator([
            (
                generators.InstanceSelector(
                    Region,
                    limit_choices_to={'public': True},
                ),
                4,
            ),
            (
                generators.InstanceGenerator(
                    RegionAutoFixture(Region, field_values={'public': False})
                ),
                2,
            ),
        ])
        regions = [region_generator.generate()
                   for _ in range(random.randint(1, 3))]
        instance.regions.set(list(regions))


register(Project, ProjectAutoFixture)
