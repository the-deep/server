from utils.extractor import extractors
from utils.extractor import thumbnailers

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

THUMBNAILERS = {
    HTML: thumbnailers.WebThumbnailer,
    PDF: thumbnailers.DocThumbnailer,
    DOCX: thumbnailers.DocThumbnailer,
    PPTX: thumbnailers.DocThumbnailer,
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

    def get_thumbnail(self):
        """
        Create thumbnail for the document

        Returns thumbnail file
        """
        thumbnailer = THUMBNAILERS.get(self.type)
        if thumbnailer:
            if self.type is HTML:
                return thumbnailer(self.params.url, self.type).get_thumbnail()
            else:
                return thumbnailer(self.doc, self.type).get_thumbnail()

        return None
