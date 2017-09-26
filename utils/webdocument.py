import requests
import tempfile
from django.conf import settings

from ..common import (write_file, USER_AGENT)
from .extractor import extractors

HTML = 'html'
PDF = 'pdf'
DOCX = 'docx'
PPTX = 'pptx'

EXTRACTORS = {
    HTML: extractors.HtmlStripper,
    PDF: extractors.PdfStripper,
    DOCX: extractors.DocxStripper,
    PPTX: extractors.PptxStripper,
}


class WebDocument:
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

        self.type = HTML
        self.doc = None

        headers = {
            'User-Agent': USER_AGENT
        }

        try:
            r = requests.head(url, headers=headers)
        except:
            # If we can't get header, assume html and try to continue.
            r = requests.get(url, headers=headers)
            self.doc = r.content
            return

        if any(x in r.headers["content-type"] for x in self.HTML_TYPES):
            r = requests.get(url, headers=headers)
            self.doc = r.content
        else:
            fp = tempfile.NamedTemporaryFile(dir=settings.BASE_DIR)
            r = requests.get(url, stream=True, headers=headers)
            write_file(r, fp)

            self.doc = fp
            if any(x in r.headers["content-type"] for x in self.PDF_TYPES):
                self.type = PDF

            elif any(x in r.headers["content-type"] for x in self.DOCX_TYPES):
                self.type = DOCX

            elif any(x in r.headers["content-type"] for x in self.PPTX_TYPES):
                self.type = PPTX

    def simplify(self):
        extractor = EXTRACTORS.get(self.type)
        if extractor:
            return extractor(self.doc).simplify()
        return '', []
