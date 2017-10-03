from utils.extractor import extractors

HTML = 'html'
PDF = 'pdf'
DOCX = 'docx'
PPTX = 'pptx'

EXTRACTORS = {
    HTML: extractors.HtmlExtractor,
    PDF: extractors.PdfExtractor,
    DOCX: extractors.DocxExtractor,
    PPTX: extractors.PptxExtractor,
}


class Document:
    """
    A wrapper for document

    Helps extract any type of file
    """
    def __init__(self, doc, type):
        self.type = type
        self.doc = doc

    def extract(self):
        """
        Extracts text and images from the document

        Returns a tuple of text as string and images as list
        """
        extractor = EXTRACTORS.get(self.type)
        if extractor:
            return extractor(self.doc).extract()
        return '', []
