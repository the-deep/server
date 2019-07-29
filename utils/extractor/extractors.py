from .exception import ExtractError
from .formats.html import process as html_extract
from .formats.pdf import process as pdf_extract
from .formats.docx import (
    process as docx_extract,
    pptx_process as pptx_extract,
    msword_process as msword_extract
)


class BaseExtractor:
    """
    Basic Extractor Class
    Take doc
    Verify
    Simlify
    """
    def __init__(self, doc, params=None):
        self.doc = doc
        self.params = params

    def extract(self):
        """
        Return text, images
        """
        self.verify()
        return self.__class__.EXTRACT_METHOD(self.doc)

    def verify(self):
        if not self.doc:
            raise ExtractError(self.ERROR_MSG)
        if not hasattr(self.__class__, 'EXTRACT_METHOD'):
            raise ExtractError(
                "Class '{}' have no EXTRACT_METHOD Method".
                format(self.__class__.__name__)
            )


class HtmlExtractor(BaseExtractor):
    """
    Extractor class to extract HTML documents.
    """
    ERROR_MSG = "Not a html document"
    EXTRACT_METHOD = html_extract

    def extract(self):
        self.verify()
        url = self.params.get('url') if self.params else None
        return self.__class__.EXTRACT_METHOD(self.doc, url)


class PdfExtractor(BaseExtractor):
    """
    Extractor class to extract PDF documents.
    """
    ERROR_MSG = "Not a pdf document"
    EXTRACT_METHOD = pdf_extract


class DocxExtractor(BaseExtractor):
    """
    Extractor class to extract Docx documents.
    """
    ERROR_MSG = "Not a docx document"
    EXTRACT_METHOD = docx_extract


class PptxExtractor(BaseExtractor):
    """
    Extractor class to extract PPTX documents.
    """
    ERROR_MSG = "Not a pptx document"
    EXTRACT_METHOD = pptx_extract


class MswordExtractor(BaseExtractor):
    """
    Extractor class to extract msword documents.
    """
    ERROR_MSG = "Not a msword (.doc) document"
    EXTRACT_METHOD = msword_extract
