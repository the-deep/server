from drf_dynamic_fields import DynamicFieldsMixin
from rest_framework import serializers
from rest_framework.exceptions import APIException

from django.conf import settings
from django.core.files.uploadedfile import InMemoryUploadedFile

from deep.serializers import RemoveNullFieldsMixin
from user_resource.serializers import UserResourceSerializer
from utils.external_storages.google_drive import download as g_download
from utils.external_storages.dropbox import download as d_download
from .models import File, FilePreview

import os


class SimpleFileSerializer(RemoveNullFieldsMixin,
                           serializers.ModelSerializer):
    title = serializers.CharField(required=False, read_only=True)
    file = serializers.FileField(required=False, read_only=True)
    mime_type = serializers.CharField(required=False, read_only=True)

    class Meta:
        model = File
        fields = ('id', 'title', 'file', 'mime_type')


class FileSerializer(RemoveNullFieldsMixin,
                     DynamicFieldsMixin, UserResourceSerializer):
    class Meta:
        model = File
        fields = ('__all__')

    # Validations
    def validate_file(self, file):
        extension = os.path.splitext(file.name)[1][1:]
        if file.content_type not in settings.DEEP_SUPPORTED_MIME_TYPES and \
                extension not in settings.DEEP_SUPPORTED_EXTENSIONS:
            raise serializers.ValidationError(
                'Unsupported file type {}'.format(file.content_type))
        return file

    def create(self, validated_data):
        validated_data['mime_type'] = validated_data.get('file').content_type
        return super(FileSerializer, self).create(validated_data)


class GoogleDriveFileSerializer(RemoveNullFieldsMixin,
                                UserResourceSerializer):
    access_token = serializers.CharField(write_only=True)
    file_id = serializers.CharField(write_only=True)
    mime_type = serializers.CharField()

    class Meta:
        model = File
        fields = ('__all__')

    def create(self, validated_data):
        title = validated_data.get('title')
        access_token = validated_data.pop('access_token')
        file_id = validated_data.pop('file_id')
        mime_type = validated_data.get('mime_type', '')

        file = g_download(
            file_id,
            mime_type,
            access_token,
            settings.DEEP_SUPPORTED_MIME_TYPES,
            APIException,
        )

        # TODO: is this good?
        validated_data['file'] = InMemoryUploadedFile(
            file, None, title, mime_type, None, None
        )

        return super(GoogleDriveFileSerializer, self).create(validated_data)


class DropboxFileSerializer(RemoveNullFieldsMixin,
                            UserResourceSerializer):
    file_url = serializers.CharField(write_only=True)

    class Meta:
        model = File
        fields = ('__all__')

    def create(self, validated_data):
        title = validated_data.get('title')
        file_url = validated_data.pop('file_url')

        file, mime_type = d_download(
            file_url,
            settings.DEEP_SUPPORTED_MIME_TYPES,
            APIException,
        )

        # TODO: is this good?
        validated_data['file'] = InMemoryUploadedFile(
            file, None, title, mime_type, None, None
        )

        validated_data['mime_type'] = mime_type

        return super(DropboxFileSerializer, self).create(validated_data)


class FilePreviewSerializer(RemoveNullFieldsMixin,
                            DynamicFieldsMixin, serializers.ModelSerializer):
    class Meta:
        model = FilePreview
        fields = ('id', 'text', 'ngrams', 'extracted')
