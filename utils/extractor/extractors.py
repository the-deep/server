from .exception import StripError
from .html import process as html_simplify
from .pdf import process as pdf_simplify
from .docx import (
    process as docx_simplify,
    pptx_process as pptx_simplify
)


class BaseStripper:
    """
    Basic Stripper Class
    Take doc
    Verify
    Simlify
    """
    def __init__(self, doc):
        self.doc = doc

    def simplify(self):
        """
        Return text, images
        """
        self.verify()
        return self.SIMPLIFIER(self.doc)

    def verify(self):
        if not self.doc:
            raise StripError(self.ERROR_MSG)


class HtmlStripper(BaseStripper):
    """
    Stripper class to simplify HTML documents.
    """
    ERROR_MSG = "Not a html document"
    SIMPLIFIER = html_simplify


class PdfStripper(BaseStripper):
    """
    Stripper class to simplify PDF documents.
    """
    ERROR_MSG = "Not a pdf document"
    SIMPLIFIER = pdf_simplify


class DocxStripper(BaseStripper):
    """
    Stripper class to simplify Docx documents.
    """
    ERROR_MSG = "Not a docx document"
    SIMPLIFIER = docx_simplify


class PptxStripper(BaseStripper):
    """
    Stripper class to simplify PPTX documents.
    """
    ERROR_MSG = "Not a pptx document"
    SIMPLIFIER = pptx_simplify
