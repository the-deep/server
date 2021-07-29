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

    _counter = 0

    def create_widget(self, widget_id, data):
        project = self.create_project()
        widget = self.create(
            Widget,
            analysis_framework=project.analysis_framework,
            properties={'data': data},
            widget_id=widget_id,
            key=f'{widget_id}-{self._counter}'
        )
        self._counter += 1
        return widget

    def create_attribute(self, widget_id, widget_data, attr_data):
        widget = self.create_widget(widget_id, widget_data)
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
        expected_c_response = expected_c_response or {}
        widget, attribute = self.create_attribute(widget_id, widget_data, attr_data)
        widget_data = widget.properties and widget.properties.get('data')
        data = attribute.data or {}
        c_resposne = self.get_data_selector(widget_id)(
            widgets_meta, widget, data, widget_data,
        ) or {}
        if widget_id in ('scaleWidget',):
            # new key 'scale' is appended
            self.assertTrue(expected_c_response.items() <= c_resposne.items(),
                            (expected_c_response.items(), c_resposne.items()))
        elif widget_id in ('conditionalWidget',):
            # custom handler for scale widget again
            if expected_c_response.get('type') == 'scaleWidget':
                self.assertTrue(expected_c_response.get('value').items() <= c_resposne.get('value').items(),
                                (expected_c_response.items(), c_resposne.items()))
            else:
                self.assertEqual(expected_c_response, c_resposne)
        else:
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
