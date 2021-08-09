from django.conf import settings
from rest_framework import (
    viewsets,
    response,
    permissions,
)
from deep.permissions import IsSuperAdmin
from .serializers import LanguageSerializer, StringsSerializer
from .models import String, LinkCollection


class LanguageViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated,
                          IsSuperAdmin]

    def retrieve(self, request, pk=None, version=None):
        code = pk
        languages = settings.LANGUAGES
        language = next((_lang for _lang in languages if _lang[0] == code), None)

        def get_links(collection):
            return collection.links.filter(language=code)

        obj = {
            'code': code,
            'title': language[1],
            'strings': String.objects.filter(language=code),
            'links': {
                link_collection.key: get_links(link_collection)
                for link_collection in LinkCollection.objects.all()
            },
        }

        return response.Response(StringsSerializer(obj).data)

    def list(self, request, version=None):
        languages = [
            {
                'code': _lang[0],
                'title': _lang[1],
            }
            for _lang in settings.LANGUAGES
        ]
        serializer = LanguageSerializer(
            languages,
            many=True,
        )
        results = serializer.data

        return response.Response({
            'count': len(results),
            'results': results,
        })

    def update(self, request, pk=None, version=None):
        serializer = StringsSerializer(data={
            'code': pk,
            **request.data,
        })
        serializer.save()
        return self.retrieve(request, pk=pk)
