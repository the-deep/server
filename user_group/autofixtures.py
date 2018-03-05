from autofixture import register, generators, AutoFixture
from .models import UserGroup, GroupMembership


class UserGroupAutoFixture(AutoFixture):
    overwrite_defaults = True
    field_values = {
        'display_picture': None,
        'global_crisis_monitoring': False,
        'custom_project_fields': None,
    }

    def post_process_instance(self, instance, commit):
        generators.MultipleInstanceGenerator(
            AutoFixture(GroupMembership, field_values={
                'group': instance,
            }),
            min_count=2,
            max_count=5,
        ).generate()


register(UserGroup, UserGroupAutoFixture)
