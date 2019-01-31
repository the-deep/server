from deep.tests import TestCase
import autofixture

from tabular.models import Field


class TestFieldUpdateApi(TestCase):
    """
    Testing field Update, which supports only put and returns data from it's
    sheet
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.url = '/api/v1/tabular-field-update/'

    def setUp(self):
        super().setUp()
        self.field = autofixture.create_one(Field, generate_fk=True)

    def test_get_list_not_found(self):
        self.authenticate()
        resp = self.client.get(self.url)
        self.assert_404(resp)

    def test_get_instance_not_allowed(self):
        self.authenticate()
        resp = self.client.get(self.url + '1/')
        self.assert_405(resp)

    def test_post_not_allowed(self):
        self.authenticate()
        resp = self.client.post(self.url)
        self.assert_405(resp)

    def test_delete_not_allowed(self):
        self.authenticate()
        resp = self.client.delete(self.url + '1/')
        self.assert_405(resp)

    def test_put_inexistient(self):
        self.authenticate()
        data = {
            'title': 'Test',
        }
        resp = self.client.put(
            '{}{}/'.format(self.url, self.field.id + 1),
            data=data
        )
        self.assert_404(resp)

    def test_put_returns_corresponding_sheet_data(self):
        self.authenticate()
        data = {
            'title': 'Test',
            'type': Field.DATETIME,
            'options': {
                'a': 1,
                'b': 'test'
            }
        }
        resp = self.client.put(
            '{}{}/'.format(self.url, self.field.id),
            data=data
        )
        self.assert_200(resp)

        respdata = resp.json()
        assert 'fieldData' in respdata
        assert 'field' in respdata
        field = respdata['field']
        assert field['title'] == data['title']
        assert field['type'] == data['type']
        assert field['options'] == data['options']
