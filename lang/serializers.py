from django.core.exceptions import ObjectDoesNotExist
from drf_dynamic_fields import DynamicFieldsMixin
from rest_framework import serializers

from deep.serializers import RemoveNullFieldsMixin
from .models import String, Link


class LanguageSerializer(RemoveNullFieldsMixin,
                         serializers.Serializer):
    code = serializers.CharField()
    title = serializers.CharField()


class StringSerializer(RemoveNullFieldsMixin,
                       serializers.ModelSerializer):
    class Meta:
        model = String
        fields = ('id', 'value')


class LinkSerializer(RemoveNullFieldsMixin,
                     serializers.ModelSerializer):
    class Meta:
        model = Link
        fields = ('id', 'key', 'string')


# Expects a object containing 'code', title', `strings` and `links`
class StringsSerializer(RemoveNullFieldsMixin,
                        serializers.Serializer):
    code = serializers.CharField(read_only=True)
    title = serializers.CharField(read_only=True)
    strings = StringSerializer(many=True)
    links = LinkSerializer(many=True)

    strings_to_delete = serializers.ListField(child=serializers.IntegerField(),
                                              write_only=True,
                                              required=False)
    links_to_delete = serializers.ListField(child=serializers.IntegerField(),
                                            write_only=True,
                                            required=False)

    def save(self):
        code = self.initial_data['code']
        strings = self.initial_data.get('strings') or []
        links = self.initial_data.get('links') or []

        strings_to_delete = self.initial_data.get('strings_to_delete') or []
        links_to_delete = self.initial_data.get('links_to_delete') or []

        String.objects.filter(
            language=code,
            id__in=strings_to_delete,
        ).delete()

        Link.objects.filter(
            language=code,
            id__in=links_to_delete,
        ).delete()

        string_map = {}
        for string_data in strings:
            id = string_data['id']
            try:
                id = int(id)
                string = String.objects.get(id=id)
            except (ValueError, ObjectDoesNotExist):
                string = String()

            string.language = code
            string.value = string_data['value']
            string.save()

            string_map[id] = string

        for link_data in links:
            id = link_data['id']
            try:
                id = int(id)
                link = Link.objects.get(id=id)
            except (ValueError, ObjectDoesNotExist):
                link = Link()

            link.language = code
            link.key = link_data['key']

            str_id = link_data['string']
            link.string = string_map.get(str_id) or \
                String.objects.get(id=str_id)
            link.save()
