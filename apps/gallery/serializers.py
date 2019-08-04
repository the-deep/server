from drf_dynamic_fields import DynamicFieldsMixin
from rest_framework import serializers
from rest_framework.exceptions import APIException

from django.core.files.uploadedfile import InMemoryUploadedFile

from deep.serializers import RemoveNullFieldsMixin, URLCachedFileField
import deep.documents_types as deep_doc_types
from user_resource.serializers import UserResourceSerializer
from utils.external_storages.google_drive import download as g_download
from utils.external_storages.dropbox import download as d_download
from utils.extractor.formats.docx import get_pages_in_docx
from utils.extractor.formats.pdf import get_pages_in_pdf
from utils.common import calculate_md5
from .models import File, FilePreview

import os
import logging

logger = logging.getLogger(__name__)

FILE_READONLY_FIELDS = ('metadata', 'mime_type',)


class SimpleFileSerializer(RemoveNullFieldsMixin,
                           serializers.ModelSerializer):
    title = serializers.CharField(required=False, read_only=True)
    file = URLCachedFileField(required=False, read_only=True)
    mime_type = serializers.CharField(required=False, read_only=True)

    class Meta:
        model = File
        fields = ('id', 'title', 'file', 'mime_type')
        read_only_fields = FILE_READONLY_FIELDS


class FileSerializer(RemoveNullFieldsMixin,
                     DynamicFieldsMixin, UserResourceSerializer):
    file = URLCachedFileField(required=True, read_only=False)

    class Meta:
        model = File
        fields = ('__all__')
        read_only_fields = FILE_READONLY_FIELDS

    # Validations
    def validate_file(self, file):
        extension = os.path.splitext(file.name)[1][1:]
        if file.content_type not in deep_doc_types.DEEP_SUPPORTED_MIME_TYPES\
                and extension not in deep_doc_types.DEEP_SUPPORTED_EXTENSIONS:
            raise serializers.ValidationError(
                'Unsupported file type {}'.format(file.content_type))
        return file

    def _get_metadata(self, file):
        metadata = {'md5_hash': calculate_md5(file.file)}
        mime_type = file.content_type
        if mime_type in deep_doc_types.PDF_MIME_TYPES:
            metadata.update({
                'pages': get_pages_in_pdf(file.file),
            })
        elif mime_type in deep_doc_types.DOCX_MIME_TYPES:
            metadata.update({
                'pages': get_pages_in_docx(file.file),
            })
        return metadata

    def create(self, validated_data):
        validated_data['mime_type'] = validated_data.get('file').content_type
        try:
            validated_data['metadata'] = self._get_metadata(
                validated_data.get('file')
            )
        except Exception:
            logger.error('File create Failed!!', exc_info=True)
        return super().create(validated_data)


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
            deep_doc_types.DEEP_SUPPORTED_MIME_TYPES,
            APIException,
        )

        # TODO: is this good?
        validated_data['file'] = InMemoryUploadedFile(
            file, None, title, mime_type, None, None
        )

        return super().create(validated_data)


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
            deep_doc_types.DEEP_SUPPORTED_MIME_TYPES,
            APIException,
        )

        # TODO: is this good?
        validated_data['file'] = InMemoryUploadedFile(
            file, None, title, mime_type, None, None
        )

        validated_data['mime_type'] = mime_type

        return super().create(validated_data)


class FilePreviewSerializer(RemoveNullFieldsMixin,
                            DynamicFieldsMixin, serializers.ModelSerializer):
    class Meta:
        model = FilePreview
        fields = ('id', 'text', 'ngrams', 'extracted')
