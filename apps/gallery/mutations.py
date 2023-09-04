import graphene

from utils.graphene.mutation import (
    generate_input_type_for_serializer,
    PsGrapheneMutation,
)

from .models import File
from .schema import GalleryFileType
from .serializers import (
    FileSerializer
)

FileUploadInputType = generate_input_type_for_serializer(
    'FileUploadInputType',
    serializer_class=FileSerializer
)


class UploadFile(PsGrapheneMutation):
    class Arguments:
        data = FileUploadInputType(required=True)

    result = graphene.Field(GalleryFileType)
    serializer_class = FileSerializer
    model = File
    permissions = []


class Mutation():
    file_upload = UploadFile.Field()
