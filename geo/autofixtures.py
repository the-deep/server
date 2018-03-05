from autofixture import register, AutoFixture
from .models import Region


class RegionAutoFixture(AutoFixture):
    overwrite_defaults = True
    field_values = {
        'regional_groups': None,
        'key_figures': None,
        'population_data': None,
        'media_sources': None,
    }

    # def post_process_instance(self, instance, commit):
    #     pass


register(Region, RegionAutoFixture)
