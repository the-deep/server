from user_resource.serializers import UserResourceSerializer
from .models import Lead


class LeadSerializer(UserResourceSerializer):
    """
    Lead Model Serializer
    """
    class Meta:
        model = Lead
        fields = ('__all__')
