from rest_framework import serializers
from .models import Lead


class LeadSerializer(serializers.ModelSerializer):
    """
    Lead Model Serializer
    """
    class Meta:
        model = Lead
        fields = ('__all__')
