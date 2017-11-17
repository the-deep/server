import httplib2

from utils.common import USER_AGENT
from apiclient import discovery
from oauth2client import client
import tempfile

from apiclient.http import MediaIoBaseDownload

# Google Specific Mimetypes
GDOCS = 'application/vnd.google-apps.document'
GSLIDES = 'application/vnd.google-apps.presentation'
GSHEETS = 'application/vnd.google-apps.spreadsheet'

# Standard Mimetypes
DOCX = 'application/vnd.openxmlformats-officedocument.wordprocessingml.'\
       'document'
PPT = 'application/vnd.openxmlformats-officedocument.presentationml.'\
      'presentation'
EXCEL = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'

# Goggle Specific mimetypes to Standard Mimetypes mapping
GOOLE_DRIVE_EXPORT_MAP = {
    GDOCS: DOCX,
    GSLIDES: PPT,
    GSHEETS: EXCEL,
}


def get_credentials(access_token):
    credentials = client.AccessTokenCredentials(access_token, USER_AGENT)
    return credentials


def download(
        file_id,
        mimeType,
        access_token,
        SUPPORTED_MIME_TYPES):
    """
    Download/Export file from google drive

    params:
        fileId: file id from google drive
        mimeType: file mime types from google drive
        access_token: access token provided by google drive
        SUPPORTED_MIME_TYPES: which types of file to download
    """

    credentials = get_credentials(access_token)
    http = credentials.authorize(httplib2.Http())

    service = discovery.build('drive', 'v3', http=http)

    if mimeType in SUPPORTED_MIME_TYPES:
        # Directly dowload the file
        request = service.files().get_media(fileId=file_id)
    else:
        export_mime_type = GOOLE_DRIVE_EXPORT_MAP.get(mimeType)

        if export_mime_type and export_mime_type in SUPPORTED_MIME_TYPES:
            # Convert the google files to supported file
            request = service.files().export_media(
                fileId=file_id,
                mimeType=export_mime_type
            )
        else:
            return None

    outfp = tempfile.TemporaryFile("wb+")
    downloader = MediaIoBaseDownload(outfp, request)
    done = False
    while done is False:
        status, done = downloader.next_chunk()
        # print('Download %d%%.' % int(status.progress() * 100))

    return outfp


"""
# TODO: Only for testing, remove this
DEEP_SUPPORTED_MIME_TYPES = [
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'application/rtf', 'text/plain', 'font/otf', 'application/pdf',
    'application/vnd.openxmlformats-officedocument.presentationml.'
    'presentation',
    'application/vnd.ms-powerpoint', 'application/vnd.ms-excel',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    'text/csv', 'image/png', 'image/jpeg', 'image/fig',
    'application/json', 'application/xml', 'application/msword',
]

if __name__ == '__main__':
    file_id = ''
    mimeType = ''
    access_token = ''

    print(download(
        file_id, mimeType,
        access_token,
        DEEP_SUPPORTED_MIME_TYPES,
    ))
"""
