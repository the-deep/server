from django.contrib.auth.models import User
from rest_framework import serializers
from user.models import Profile


class UserSerializer(serializers.ModelSerializer):
    organization = serializers.CharField(source='profile.organization',
                                         allow_blank=True)
    display_picture = serializers.FileField(source='profile.display_picture',
                                            allow_empty_file=True,
                                            required=False)

    class Meta:
        model = User
        fields = ('id', 'username', 'password', 'first_name', 'last_name',
                  'email', 'organization', 'display_picture',)
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        profile_data = validated_data.pop('profile', None)
        user = super(UserSerializer, self).create(validated_data)
        user.set_password(validated_data['password'])
        user.save()
        self.update_or_create_profile(user, profile_data)
        return user

    def update(self, instance, validated_data):
        profile_data = validated_data.pop('profile', None)
        user = super(UserSerializer, self).update(instance, validated_data)
        if 'password' in validated_data:
            user.set_password(validated_data['password'])
            user.save()
        self.update_or_create_profile(user, profile_data)
        return user

    def update_or_create_profile(self, user, profile_data):
        Profile.objects.update_or_create(user=user, defaults=profile_data)


# EOF
