from user_resource.serializers import UserResourceSerializer
from .models import File


class FileSerializer(UserResourceSerializer):
    class Meta:
        model = File
        fields = ('__all__')
