from utils.extractor import extractors

HTML = 'html'
PDF = 'pdf'
DOCX = 'docx'
PPTX = 'pptx'
MSWORD = 'doc'

EXTRACTORS = {
    HTML: extractors.HtmlExtractor,
    PDF: extractors.PdfExtractor,
    DOCX: extractors.DocxExtractor,
    PPTX: extractors.PptxExtractor,
    MSWORD: extractors.MswordExtractor,
}


class Document:
    """
    A wrapper for document

    Helps extract any type of file
    """

    def __init__(self, doc, type, params=None):
        self.type = type
        self.doc = doc
        self.params = params

    def extract(self):
        """
        Extracts text and images from the document

        Returns a tuple of text as string, images as list and page_count as int
        """
        extractor = EXTRACTORS.get(self.type)
        if extractor:
            return extractor(self.doc, self.params).extract()
        return '', [], 1
