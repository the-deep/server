import graphene
from graphene_django import DjangoObjectType

from utils.graphene.types import FileFieldType
from .models import File


class GalleryFileType(DjangoObjectType):
    class Meta:
        model = File
        fields = (
            'id',
            # 'uuid',
            'title',
            'mime_type',
            'metadata',
        )
    file = graphene.Field(FileFieldType)

    @staticmethod
    def resolve_file(root, info, **_):
        if root.file:
            return root.file
