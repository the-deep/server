from user_resource.serializers import UserResourceSerializer
from .models import File


class FileSerializer(UserResourceSerializer):
    class Meta:
        model = File
        fields = ('__all__')

    def create(self, validated_data):
        file = super(FileSerializer, self).create(validated_data)
        file.permitted_users.add(self.context['request'].user)
        return file
