import graphene
from graphene_django import DjangoObjectType

from utils.graphene.fields import FileField
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
    file = graphene.Field(FileField)
