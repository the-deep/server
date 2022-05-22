import graphene
from graphene_django import DjangoObjectType

from utils.graphene.types import FileFieldType
from .models import File


class GalleryFileType(DjangoObjectType):
    class Meta:
        model = File
        only_fields = (
            'id',
            'title',
            'mime_type',
            'metadata',
        )
    file = graphene.Field(FileFieldType)

    @staticmethod
    def resolve_file(root, info, **_):
        if root.file:
            return root.file


class PublicGalleryFileType(DjangoObjectType):
    class Meta:
        model = File
        skip_registry = True
        only_fields = ('title', 'mime_type',)
    file = graphene.Field(FileFieldType)

    @staticmethod
    def resolve_file(root, info, **_):
        if root.file:
            return root.file
