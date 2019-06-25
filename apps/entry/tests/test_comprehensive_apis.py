from deep.tests import TestCase

from analysis_framework.models import (
    Widget,
)
from entry.models import (
    Attribute,
)
from entry.widgets.store import widget_store


# NOTE: This structure and value are set through https://github.com/the-deep/client
WIDGET_DATA = {
    'selectWidget': {
        'options': [
            {'key': 'option-1', 'label': 'Option 1'},
            {'key': 'option-2', 'label': 'Option 2'},
            {'key': 'option-3', 'label': 'Option 3'}
        ]
    },
    'multiselectWidget': {
        'options': [
            {'key': 'option-1', 'label': 'Option 1'},
            {'key': 'option-2', 'label': 'Option 2'},
            {'key': 'option-3', 'label': 'Option 3'}
        ]
    },
    'scaleWidget': {
        'scale_units': [
            {'key': 'scale-1', 'color': '#470000', 'label': 'Scale 1'},
            {'key': 'scale-2', 'color': '#a40000', 'label': 'Scale 2'},
            {'key': 'scale-3', 'color': '#d40000', 'label': 'Scale 3'}
        ]
    },
}

# NOTE: This structure and value are set through https://github.com/the-deep/client
ATTRIBUTE_DATA = {
    'selectWidget': [{
        'data': {'value': 'option-3'},
        'response': 'Option 3',
    }, {
        'data': {'value': 'option-5'},
        'response': None,
    }],
    'multiselectWidget': [{
        'data': {'value': ['option-3', 'option-1']},
        'response': ['Option 3', 'Option 1'],
    }, {
        'data': {'value': ['option-5', 'option-1']},
        'response': ['Option 1'],
    }],
    'scaleWidget': [{
        'data': {'value': 'scale-1'},
        'response': 'Scale 1',
    }, {
        'data': {'value': 'scale-5'},
        'response': None,
    }],
}


class ComprehensiveEntryApiTest(TestCase):
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

    def assertAttributeValue(self, widget_id, widget_data, attr_data, expected_response):
        widget, attribute = self.create_attribute(widget_data, attr_data)
        widget_data = widget.properties and widget.properties.get('data')
        data = attribute.data or {}
        self.assertEqual(
            self.get_data_selector(widget_id)(
                widget, data, widget_data,
            ),
            expected_response,
        )

    def _test_widget(self, widget_id):
        widget_data = WIDGET_DATA[widget_id]

        for attribute_data in ATTRIBUTE_DATA[widget_id]:
            attr_data = attribute_data['data']
            expected_response = attribute_data['response']
            self.assertAttributeValue(widget_id, widget_data, attr_data, expected_response)

    def test_select_widget(self):
        widget_id = 'selectWidget'
        self._test_widget(widget_id)

    def test_multiselect_widget(self):
        widget_id = 'multiselectWidget'
        self._test_widget(widget_id)

    def test_scale_widget(self):
        widget_id = 'scaleWidget'
        self._test_widget(widget_id)
