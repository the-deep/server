from django.conf import settings
from deep.tests import TestCase
from lang.models import String, LinkCollection, Link


class LangApiTests(TestCase):
    def test_update_language(self):
        lang_code = settings.LANGUAGE_CODE
        url = '/api/v1/languages/{}/'.format(lang_code)

        # First test creating
        data = {
            'strings': [
                {'id': 's_1', 'value': 's1', 'action': 'add'},
                {'id': 's_2', 'value': 's2', 'action': 'add'},
            ],
            'links': {
                'group1': [
                    {'key': 'l_1', 'string': 's_1', 'action': 'add'},
                    {'key': 'l_2', 'string': 's_2', 'action': 'add'},
                ],
                'group2': [
                    {'key': 'l_1', 'string': 's_2', 'action': 'add'},
                ],
            },
        }

        self.authenticate()
        response = self.client.put(url, data)
        self.assert_200(response)

        s1 = String.objects.filter(value='s1').first()
        s2 = String.objects.filter(value='s2').first()
        self.assertIsNotNone(s1)
        self.assertIsNotNone(s2)

        group1 = LinkCollection.objects.filter(key='group1').first()
        group2 = LinkCollection.objects.filter(key='group2').first()
        self.assertIsNotNone(group1)
        self.assertIsNotNone(group2)

        l1 = Link.objects.filter(link_collection=group1,
                                 key='l_1', string=s1).first()
        l2 = Link.objects.filter(link_collection=group1,
                                 key='l_2', string=s2).first()
        l3 = Link.objects.filter(link_collection=group2,
                                 key='l_1', string=s2).first()
        self.assertIsNotNone(l1)
        self.assertIsNotNone(l2)
        self.assertIsNotNone(l3)

        # Then test updating, deleting and creating
        data = {
            'strings': [
                {'id': s1.id, 'value': 's1 new', 'action': 'edit'},
                {'id': s2.id, 'action': 'delete'},
                {'id': 's_3', 'value': 's3', 'action': 'add'},
            ],
            'links': {
                'group1': [
                    {'key': 'l_1', 'action': 'delete'},
                    {'key': 'l_2', 'string': 's_3', 'action': 'edit'},
                ],
                'group2': [
                    {'key': 'l_1', 'string': s1.id, 'action': 'edit'},
                ],
                'group3': [],
            },
        }

        self.authenticate()
        response = self.client.put(url, data)
        self.assert_200(response)

        s1 = String.objects.filter(id=s1.id).first()
        s2 = String.objects.filter(id=s2.id).first()
        s3 = String.objects.filter(value='s3').first()
        self.assertEqual(s1.value, 's1 new')
        self.assertIsNone(s2)
        self.assertIsNotNone(s3)

        group1 = LinkCollection.objects.filter(key='group1').first()
        group2 = LinkCollection.objects.filter(key='group2').first()
        group3 = LinkCollection.objects.filter(key='group3').first()
        self.assertIsNotNone(group1)
        self.assertIsNotNone(group2)
        self.assertIsNone(group3)

        l1 = Link.objects.filter(id=l1.id).first()
        l2 = Link.objects.filter(id=l2.id).first()
        l3 = Link.objects.filter(id=l3.id).first()
        self.assertIsNone(l1)
        self.assertEquals(l2.string, s3)
        self.assertEquals(l3.string, s1)
