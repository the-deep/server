from rest_framework import serializers

from .models import DeduplicationRequest


class DeduplicationRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeduplicationRequest
        exclude = ["error", "result"]
