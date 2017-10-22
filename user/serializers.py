from django.contrib.auth.models import User
from drf_dynamic_fields import DynamicFieldsMixin
from rest_framework import serializers

from user.models import Profile
from gallery.models import File


class UserSerializer(DynamicFieldsMixin, serializers.ModelSerializer):
    organization = serializers.CharField(source='profile.organization',
                                         allow_blank=True)
    display_picture = serializers.PrimaryKeyRelatedField(
        source='profile.display_picture',
        queryset=File.objects.all(),
        allow_null=True,
    )
    display_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('id', 'username', 'password', 'first_name', 'last_name',
                  'display_name',
                  'email', 'organization', 'display_picture',)
        extra_kwargs = {'password': {'write_only': True}}

    def get_display_name(self, user):
        return user.profile.get_display_name()

    def create(self, validated_data):
        profile_data = validated_data.pop('profile', None)
        user = super(UserSerializer, self).create(validated_data)
        user.set_password(validated_data['password'])
        user.save()
        user.profile = self.update_or_create_profile(user, profile_data)
        return user

    def update(self, instance, validated_data):
        profile_data = validated_data.pop('profile', None)
        user = super(UserSerializer, self).update(instance, validated_data)
        if 'password' in validated_data:
            user.set_password(validated_data['password'])
            user.save()
        user.profile = self.update_or_create_profile(user, profile_data)
        return user

    def update_or_create_profile(self, user, profile_data):
        profile, created = Profile.objects.update_or_create(
            user=user, defaults=profile_data
        )
        return profile
