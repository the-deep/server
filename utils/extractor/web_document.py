import requests
import tempfile
from django.conf import settings

from utils.common import (write_file, DEFAULT_HEADERS)
from .document import (
    Document,
    MIME_TYPES,
    HTML, PDF, DOCX, PPTX,
)


class WebDocument(Document):
    """
    Web documents can be html or pdf.
    Takes url
    Gives document and type
    """
    HTML_TYPES = [MIME_TYPES[HTML], 'text/plain']
    PDF_TYPES = [MIME_TYPES[PDF], ]
    DOCX_TYPES = [MIME_TYPES[DOCX], ]
    PPTX_TYPES = [MIME_TYPES[PPTX], ]

    def __init__(self, url):
        type = HTML
        doc = None
        mime_type = None

        try:
            r = requests.head(url, headers=DEFAULT_HEADERS)
        except requests.exceptions.RequestException:
            # If we can't get header, assume html and try to continue.
            r = requests.get(url, headers=DEFAULT_HEADERS)
            doc = r.content
            super().__init__(doc, type)
            return

        mime_type = r.headers.get('content-type')
        if not mime_type or \
                any(x in mime_type for x in self.HTML_TYPES):
            r = requests.get(url, headers=DEFAULT_HEADERS)
            doc = r.content
        else:
            fp = tempfile.NamedTemporaryFile(dir=settings.BASE_DIR)
            r = requests.get(url, stream=True, headers=DEFAULT_HEADERS)
            write_file(r, fp)

            doc = fp
            if any(x in mime_type for x in self.PDF_TYPES):
                type = PDF

            elif any(x in mime_type for x in self.DOCX_TYPES):
                type = DOCX

            elif any(x in mime_type for x in self.PPTX_TYPES):
                type = PPTX

        super().__init__(doc, type, mime_type)
