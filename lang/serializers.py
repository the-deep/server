from rest_framework import serializers

from deep.serializers import RemoveNullFieldsMixin
from .models import String, Link, LinkCollection


class LanguageSerializer(RemoveNullFieldsMixin,
                         serializers.Serializer):
    code = serializers.CharField()
    title = serializers.CharField()


class StringSerializer(RemoveNullFieldsMixin,
                       serializers.ModelSerializer):
    action = serializers.CharField(write_only=True)

    class Meta:
        model = String
        fields = ('id', 'value', 'action')


class LinkSerializer(RemoveNullFieldsMixin,
                     serializers.ModelSerializer):
    action = serializers.CharField(write_only=True)

    class Meta:
        model = Link
        fields = ('id', 'key', 'string', 'action')


# Override DictField with partial value set to solve a DRF Bug
class DictField(serializers.DictField):
    partial = False


# Expects a object containing 'code', title', `strings` and `links`
class StringsSerializer(RemoveNullFieldsMixin,
                        serializers.Serializer):
    code = serializers.CharField(read_only=True)
    title = serializers.CharField(read_only=True)
    strings = StringSerializer(many=True)
    links = DictField(child=LinkSerializer(many=True))

    def save(self):
        code = self.initial_data['code']
        strings = self.initial_data.get('strings') or []
        link_collections = self.initial_data.get('links') or {}

        string_map = {}
        for string_data in strings:
            action = string_data['action']
            id = string_data['id']

            if action == 'add':
                string = String()
            else:
                string = String.objects.get(id=id)

            if action == 'delete':
                string.delete()
                continue

            string.language = code
            string.value = string_data['value']
            string.save()

            string_map[id] = string

        for key, links in link_collections.items():
            collection, _ = LinkCollection.objects.get_or_create(
                key=key
            )
            for link_data in links:
                action = link_data['action']
                id = link_data['id']

                if action == 'add':
                    link = Link()
                else:
                    link = Link.objects.get(id=id)

                if action == 'delete':
                    link.delete()
                    continue

                link.language = code
                link.link_collection = collection
                link.key = link_data['key']

                str_id = link_data['string']
                link.string = string_map.get(str_id) or \
                    String.objects.get(id=str_id)
                link.save()
