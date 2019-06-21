# from unittest.mock import Mock, patch

from deep.tests import TestCase

from ary.models import Assessment, AssessmentTemplate
from ary.export import (
    normalize_assessment,
    get_export_data,
)


class TestExportStructure(TestCase):
    fixtures = ['apps/ary/tests/fixtures/ary_template_data.json']

    def setUp(self):
        # There is only one template
        self.template = AssessmentTemplate.objects.first()

    def test_get_export_data(self):
        assert False
