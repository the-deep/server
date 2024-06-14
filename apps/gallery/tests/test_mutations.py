import json

from django.core.files.temp import NamedTemporaryFile
from gallery.models import File
from graphene_file_upload.django.testing import GraphQLFileUploadTestCase
from user.factories import UserFactory

from utils.graphene.tests import GraphQLTestCase


class TestUploadFileMutation(GraphQLFileUploadTestCase, GraphQLTestCase):
    UPLOAD_FILE = """
        mutation MyMutation ($data: FileUploadInputType!) {
                 fileUpload(data: $data) {
                 ok
                 errors
                 result {
                  id
                  file {
                      name
                      url
                  }
                }
            }
        }
"""

    def setUp(self):
        super().setUp()
        self.variables = {"data": {"title": "test", "file": None}}
        self.user = UserFactory.create()
        self.force_login(self.user)

    def test_upload_file(self):
        file_text = b"preview image text"
        with NamedTemporaryFile(suffix=".jpeg") as t_file:
            t_file.write(file_text)
            t_file.seek(0)
            response = self._client.post(
                "/graphql",
                data={
                    "operations": json.dumps({"query": self.UPLOAD_FILE, "variables": self.variables}),
                    "t_file": t_file,
                    "map": json.dumps({"t_file": ["variables.data.file"]}),
                },
            )
        content = response.json()
        self.assertResponseNoErrors(response)
        created_by_user = File.objects.get(id=content["data"]["fileUpload"]["result"]["id"]).created_by
        self.assertTrue(content["data"]["fileUpload"]["ok"], content)
        self.assertTrue(content["data"]["fileUpload"]["result"]["file"]["name"])
        file_name = content["data"]["fileUpload"]["result"]["file"]["name"]
        file_url = content["data"]["fileUpload"]["result"]["file"]["url"]
        self.assertTrue(file_name.endswith(".jpeg"))
        self.assertEqual(created_by_user, self.user)
        self.assertTrue(file_url.endswith(file_name))
