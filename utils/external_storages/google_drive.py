import tempfile

import httplib2
from apiclient import discovery
from apiclient.http import MediaIoBaseDownload
from oauth2client import client
from rest_framework import serializers

from utils.common import USER_AGENT

# Google Specific Mimetypes
GDOCS = "application/vnd.google-apps.document"
GSLIDES = "application/vnd.google-apps.presentation"
GSHEETS = "application/vnd.google-apps.spreadsheet"

# Standard Mimetypes
DOCX = "application/vnd.openxmlformats-officedocument.wordprocessingml." "document"
PPT = "application/vnd.openxmlformats-officedocument.presentationml." "presentation"
EXCEL = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

# Goggle Specific mimetypes to Standard Mimetypes mapping
GOOGLE_DRIVE_EXPORT_MAP = {
    GDOCS: DOCX,
    GSLIDES: PPT,
    GSHEETS: EXCEL,
}


def get_credentials(access_token):
    credentials = client.AccessTokenCredentials(access_token, USER_AGENT)
    return credentials


def download(file_id, mime_type, access_token, SUPPORTED_MIME_TYPES):
    """
    Download/Export file from google drive

    params:
        fileId: file id from google drive
        mime_type: file mime types from google drive
        access_token: access token provided by google drive
        SUPPORTED_MIME_TYPES: which types of file to download
    """

    credentials = get_credentials(access_token)
    http = credentials.authorize(httplib2.Http())

    service = discovery.build("drive", "v3", http=http)

    if mime_type in SUPPORTED_MIME_TYPES:
        # Directly dowload the file
        request = service.files().get_media(fileId=file_id)
    elif mime_type in GOOGLE_DRIVE_EXPORT_MAP:
        export_mime_type = GOOGLE_DRIVE_EXPORT_MAP.get(mime_type)
        request = service.files().export_media(fileId=file_id, mimeType=export_mime_type)
    else:
        raise serializers.ValidationError("Unsupported file type {}".format(mime_type))

    outfp = tempfile.TemporaryFile("wb+")
    downloader = MediaIoBaseDownload(outfp, request)
    done = False
    while done is False:
        status, done = downloader.next_chunk()

    return outfp
