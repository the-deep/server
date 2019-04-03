import os
from .document import (
    Document,
    HTML, PDF, DOCX, PPTX, MSWORD,
)


class FileDocument(Document):
    """
    File documents can be html or pdf.
    Takes file
    Gives document and type
    """
    HTML_TYPES = ['.html', '.htm', '.txt']
    PDF_TYPES = ['.pdf', ]
    DOCX_TYPES = ['.docx', ]
    MSWORD_TYPES = ['.doc', ]
    PPTX_TYPES = ['.pptx', ]

    def __init__(self, file, name):

        type = None
        doc = file
        name, extension = os.path.splitext(name)

        if extension in self.PDF_TYPES:
            type = PDF
        elif extension in self.HTML_TYPES:
            type = HTML
        elif extension in self.DOCX_TYPES:
            type = DOCX
        elif extension in self.MSWORD_TYPES:
            type = MSWORD
        elif extension in self.PPTX_TYPES:
            type = PPTX

        super().__init__(doc, type)
