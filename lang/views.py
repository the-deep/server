from django.conf import settings
from rest_framework import (
    viewsets,
    response,
    permissions,
)
from deep.permissions import IsSuperAdmin
from .serializers import LanguageSerializer, StringsSerializer
from .models import String, Link


class LanguageViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated,
                          IsSuperAdmin]

    def retrieve(self, request, pk=None, version=None):
        code = pk
        languages = settings.LANGUAGES
        language = next((l for l in languages if l[0] == code), None)
        obj = {
            'code': code,
            'title': language[1],
            'strings': String.objects.filter(language=code),
            'links': Link.objects.filter(language=code),
        }

        return response.Response(StringsSerializer(obj).data)

    def list(self, request, version=None):
        languages = [
            {'code': l[0], 'title': l[1]}
            for l in settings.LANGUAGES
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
