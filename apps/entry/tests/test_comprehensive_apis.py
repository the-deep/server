from parameterized import parameterized

from deep.tests import TestCase

from analysis_framework.models import (
    Widget,
)
from entry.models import (
    Attribute,
)
from entry.widgets.store import widget_store

from .entry_widget_test_data import WIDGET_DATA, ATTRIBUTE_DATA


class ComprehensiveEntryApiTest(TestCase):
    """
    Test for comprehensive data lookup functions
    NOTE: This is a test based on assumption that the widget and attribute data are set same as
        WIDGET_DATA and ATTRIBUTE_DATA from deep-client.
    TODO: This test requires further integration test with deep-client.
    TODO: Add test for normal lookup for exportable and filter data
    """

    def create_widget(self, data):
        project = self.create_project()
        widget = self.create(
            Widget,
            analysis_framework=project.analysis_framework,
            properties={'data': data},
        )
        return widget

    def create_attribute(self, widget_data, attr_data):
        widget = self.create_widget(widget_data)
        attribute = self.create(
            Attribute,
            widget=widget,
            data=attr_data,
        )
        return widget, attribute

    def get_data_selector(self, widget_id):
        """
        Get Comprehensive Data Selector
        """
        return widget_store[widget_id].get_comprehensive_data

    def assertAttributeValue(self, widgets_meta, widget_id, widget_data, attr_data, expected_c_response):
        widget, attribute = self.create_attribute(widget_data, attr_data)
        widget_data = widget.properties and widget.properties.get('data')
        data = attribute.data or {}
        c_resposne = self.get_data_selector(widget_id)(
            widgets_meta, widget, data, widget_data,
        )
        self.assertEqual(expected_c_response, c_resposne)

    def _test_widget(self, widget_id):
        widget_data = WIDGET_DATA[widget_id]
        if not hasattr(self, 'widgets_meta'):
            self.widgets_meta = {}

        for attribute_data in ATTRIBUTE_DATA[widget_id]:
            attr_data = attribute_data['data']
            expected_c_response = attribute_data['c_response']
            self.assertAttributeValue(
                self.widgets_meta, widget_id, widget_data,
                attr_data, expected_c_response,
            )

    def test_comprehensive_api(self):
        self.authenticate()

        url = '/api/v1/comprehensive-entries/'
        response = self.client.get(url)
        self.assert_200(response)

        project = self.create_project()
        url = f'/api/v1/projects/{project.pk}/comprehensive-entries/'
        response = self.client.get(url)
        self.assert_200(response)

    @parameterized.expand([
        [widget_id] for widget_id, widget_meta in widget_store.items()
        if hasattr(widget_meta, 'get_comprehensive_data') and widget_id != 'geoWidget'
    ])
    def test_comprehensive_(self, widget_id):
        self.maxDiff = None
        self._test_widget(widget_id)
