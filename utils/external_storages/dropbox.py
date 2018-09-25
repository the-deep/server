import requests
from utils.common import write_file, DEFAULT_HEADERS
import tempfile


def download(file_url, SUPPORTED_MIME_TYPES, exception=None):
    """
    Download/Export file from google drive

    params:
        file_url: file url from dropbox
    """

    outfp = tempfile.NamedTemporaryFile()

    # TODO: verify url
    r = requests.get(file_url, stream=True, headers=DEFAULT_HEADERS)
    mime_type = r.headers["content-type"]

    if mime_type in SUPPORTED_MIME_TYPES:
        write_file(r, outfp)
        return outfp, mime_type

    if exception:
        raise exception('Unsupported Mime Type: ' + mime_type)
