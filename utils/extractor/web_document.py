import requests
import tempfile
from django.conf import settings

from utils.common import (write_file, DEFAULT_HEADERS)
from .document import (
    Document,
    HTML, PDF, DOCX, PPTX,
)


class WebDocument(Document):
    """
    Web documents can be html or pdf.
    Taks url Gives document and type
    """
    HTML_TYPES = ['text/html', 'text/plain']
    PDF_TYPES = ['application/pdf', ]
    DOCX_TYPES = ['application/vnd.openxmlformats-officedocument'
                  '.wordprocessingml.document', ]
    PPTX_TYPES = ['application/vnd.openxmlformats-officedocument'
                  '.presentationml.presentation', ]

    def __init__(self, url):

        type = HTML
        doc = None
        params = {'url': url}

        try:
            r = requests.head(url, headers=DEFAULT_HEADERS)
        except requests.exceptions.RequestException:
            # If we can't get header, assume html and try to continue.
            r = requests.get(url, headers=DEFAULT_HEADERS)
            doc = r.content
            super().__init__(doc, type, params=params)
            return

        if not r.headers.get('content-type') or \
                any(x in r.headers["content-type"] for x in self.HTML_TYPES):
            r = requests.get(url, headers=DEFAULT_HEADERS)
            doc = r.content
        else:
            fp = tempfile.NamedTemporaryFile(
                dir=settings.TEMP_DIR, delete=False)
            r = requests.get(url, stream=True, headers=DEFAULT_HEADERS)
            write_file(r, fp)

            doc = fp
            if any(x in r.headers["content-type"]
                   for x in self.PDF_TYPES):
                type = PDF

            elif any(x in r.headers["content-type"]
                     for x in self.DOCX_TYPES):
                type = DOCX

            elif any(x in r.headers["content-type"]
                     for x in self.PPTX_TYPES):
                type = PPTX

        super().__init__(doc, type, params=params)
