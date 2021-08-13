import json
from django.core.files.temp import NamedTemporaryFile
from utils.graphene.tests import GraphQLTestCase
from user.factories import UserFactory
from graphene_file_upload.django.testing import GraphQLFileUploadTestCase


class TestPreviewImage(GraphQLFileUploadTestCase, GraphQLTestCase):
    def setUp(self) -> None:
        self.user = UserFactory.create()
        self.upload_mutation = """
            mutation Mutation($data: AnalysisFrameworkInputType!) {
              analysisFrameworkCreate(data: $data) {
                ok
                errors
                result {
                  id
                  title
                  previewImage
                }
              }
            }
        """
        self.retrieve_af_query = """
        query RetrieveAFQuery {
          analysisFramework(id: %s) {
            id
            previewImage
          }
        }
        """
        self.variables = {
            "data": {"title": 'test', "previewImage": None}
        }
        self.force_login(self.user)

    def test_upload_preview_image(self):
        file_text = b'preview image text'
        with NamedTemporaryFile(suffix='.png') as t_file:
            t_file.write(file_text)
            t_file.seek(0)
            response = self._client.post(
                '/graphql',
                data={
                    'operations': json.dumps({
                        'query': self.upload_mutation,
                        'variables': self.variables
                    }),
                    't_file': t_file,
                    'map': json.dumps({
                        't_file': ['variables.data.previewImage']
                    })
                }
            )
        content = response.json()
        self.assertResponseNoErrors(response)
        # Test can upload image
        af_id = content['data']['analysisFrameworkCreate']['result']['id']
        self.assertTrue(content['data']['analysisFrameworkCreate']['ok'], content)
        self.assertTrue(content['data']['analysisFrameworkCreate']['result']['previewImage'])
        preview_image_name = content['data']['analysisFrameworkCreate']['result']['previewImage']
        self.assertTrue(preview_image_name.endswith('.png'))

        # Test can retrive image
        response = self.query(self.retrieve_af_query % af_id)
        content = response.json()
        self.assertTrue(content['data']['analysisFramework']['previewImage'])
        preview_image_name = content['data']['analysisFramework']['previewImage']
        self.assertTrue(preview_image_name.endswith('.png'))
