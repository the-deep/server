from autofixture import register, generators, AutoFixture
from urllib.parse import urlparse
from .models import Lead

import random


class LeadAutoFixture(AutoFixture):
    overwrite_defaults = True
    field_values = {
        'text': '',
        'url': '',
        'website': '',
        'attachment': None,
    }

    def post_process_instance(self, instance, commit):
        choice = random.randint(1, 2)
        if choice == 1:
            instance.text = generators.LoremGenerator().generate()
        else:
            instance.url = generators.URLGenerator().generate()
            instance.website = urlparse(instance.url).netloc
        instance.save()


register(Lead, LeadAutoFixture)
