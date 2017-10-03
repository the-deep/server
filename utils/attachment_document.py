import os

from utils.web_document import (
    HTML, PDF, DOCX, PPTX, EXTRACTORS
)


class AttachmentDocument:
    """
    Attachment documents can be html or pdf.
    Taks file Gives document and type
    """
    HTML_TYPES = ['.html', '.htm', '.txt']
    PDF_TYPES = ['.pdf', ]
    DOCX_TYPES = ['.docx', ]
    PPTX_TYPES = ['.pptx', ]

    def __init__(self, file, name):

        self.type = None
        self.doc = file
        name, extension = os.path.splitext(name)

        if extension in self.PDF_TYPES:
            self.type = PDF
        elif extension in self.HTML_TYPES:
            self.type = HTML
        elif extension in self.DOCX_TYPES:
            self.type = DOCX
        elif extension in self.PPTX_TYPES:
            self.type = PPTX

    def simplify(self):
        extractor = EXTRACTORS.get(self.type)
        if extractor:
            return extractor(self.doc).simplify()
        return '', []
